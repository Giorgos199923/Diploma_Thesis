let isDrawing = false;
let startX = 0,
  startY = 0;
let currentBox = null;
let drawnBoxes = { code: null, graph: null }; // Temporary storage for the current pair
let tempBoxPairs = []; // Buffer to store pairs before final submission

// Start drawing a box
function startDrawing(container, event) {
  if (event.button !== 0) return;
  event.preventDefault();
  isDrawing = true;
  startX = event.offsetX;
  startY = event.offsetY;

  currentBox = document.createElement("div");
  currentBox.classList.add("drawn-box");
  currentBox.style.left = `${startX}px`;
  currentBox.style.top = `${startY}px`;
  currentBox.style.width = "0px";
  currentBox.style.height = "0px";

  container.appendChild(currentBox);
  document.body.style.userSelect = "none"; 

  // If drawing a new code box, save the previous pair to `tempBoxPairs` (but not to the database yet)
  if (
    container.id === "code-container" &&
    drawnBoxes.code &&
    drawnBoxes.graph
  ) {
    tempBoxPairs.push({
      code: { ...drawnBoxes.code },
      graph: { ...drawnBoxes.graph },
    });
    drawnBoxes = { code: null, graph: null }; // Reset `drawnBoxes` for a new pair
  }
}

// Update box dimensions as the user draws
function updateDrawing(event) {
  if (!isDrawing) return;

  const currentX = event.offsetX;
  const currentY = event.offsetY;
  const width = currentX - startX;
  const height = currentY - startY;

  currentBox.style.width = `${width}px`;
  currentBox.style.height = `${height}px`;
}

// Finalize the drawing and store the box in `drawnBoxes`
function stopDrawing(container) {
  if (!isDrawing) return;
  isDrawing = false;
  document.body.style.userSelect = "auto";

  // Store the box data for code or graph
  if (container.id === "code-container") {
    drawnBoxes.code = currentBox.style; 
  } else if (container.id === "graph-container") {
    drawnBoxes.graph = currentBox.style; 
  }
}

document.querySelectorAll(".image-container").forEach((container) => {
  container.addEventListener("mousedown", (event) =>
    startDrawing(container, event)
  );
  container.addEventListener("mousemove", (event) => updateDrawing(event));
  container.addEventListener("mouseup", () => stopDrawing(container));
});

// "Undo" function to remove only the last drawn box without affecting completed pairs
function undoLastBox() {
  if (currentBox) {
    currentBox.remove();
    currentBox = null;
  }

  // Only remove the last drawn box, not the entire pair
  if (drawnBoxes.graph) {
    // Undo the graph box, keeping the code box intact
    drawnBoxes.graph = null;
  } else if (drawnBoxes.code) {
    // Undo the code box if it’s the last drawn box
    drawnBoxes.code = null;
  } else if (tempBoxPairs.length > 0) {
    // If both boxes were already saved to the buffer, remove the last saved pair
    tempBoxPairs.pop();
  }
}

document.getElementById("undo-button").addEventListener("click", undoLastBox);

// Function to save a box pair to the database
function saveBoxesToDatabase(boxes) {
  const formattedCodeBox = {
    left: parseInt(boxes.code.left, 10),
    top: parseInt(boxes.code.top, 10),
    width: parseInt(boxes.code.width, 10),
    height: parseInt(boxes.code.height, 10),
  };

  const formattedGraphBox = {
    left: parseInt(boxes.graph.left, 10),
    top: parseInt(boxes.graph.top, 10),
    width: parseInt(boxes.graph.width, 10),
    height: parseInt(boxes.graph.height, 10),
  };

  const data = { codeBox: formattedCodeBox, graphBox: formattedGraphBox };

  return fetch("/save_box_pair", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log("Box pair saved successfully:", data);
    })
    .catch((error) => console.error("Error saving box pair:", error));
}

// Clear all drawn boxes
function clearDrawnBoxes() {
  document.querySelectorAll(".drawn-box").forEach((box) => box.remove());
}

// Save all pairs in `tempBoxPairs` to the database in sequence on "Submit AOI"
document
  .getElementById("submit-aoi-button")
  .addEventListener("click", async function () {
    // Check if there's an incomplete pair in `drawnBoxes` and add it to `tempBoxPairs`
    if (drawnBoxes.code && drawnBoxes.graph) {
      tempBoxPairs.push({
        code: { ...drawnBoxes.code },
        graph: { ...drawnBoxes.graph },
      });
      drawnBoxes = { code: null, graph: null }; // Reset `drawnBoxes` after adding to buffer
    }

    for (const boxPair of tempBoxPairs) {
      await saveBoxesToDatabase(boxPair); // Wait for each save to complete before proceeding
    }

    tempBoxPairs = [];
    clearDrawnBoxes();
  });

//////////* Paths *//////////

document.getElementById("submit-paths").addEventListener("click", function () {
  const pathInput = document.getElementById("path-input").value;

  if (!pathInput.trim()) {
    alert("Please enter at least one path!");
    return;
  }

  const paths = pathInput
    .split("\n")
    .map((path) => path.trim())
    .filter((path) => path !== "");

  const pathSet = new Set();
  const duplicates = paths.filter((path) => {
    if (pathSet.has(path)) {
      return true;
    }
    pathSet.add(path);
    return false;
  });

  if (duplicates.length > 0) {
    alert(
      `Duplicate paths found: ${duplicates.join(
        ", "
      )}. Please remove duplicates and try again.`
    );
    return;
  }

  const pathsListContainer = document.querySelector(".paths-list");
  pathsListContainer.innerHTML = "";

  paths.forEach((path) => {
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.classList.add("path-checkbox");
    checkbox.dataset.path = path;

    label.appendChild(checkbox);
    label.append(` ${path}`);

    const commentBox = document.createElement("textarea");
    commentBox.classList.add("comment-box");
    commentBox.rows = 2;
    commentBox.cols = 20;
    commentBox.placeholder = "Enter comments here...";

    pathsListContainer.appendChild(label);
    pathsListContainer.appendChild(document.createElement("br"));
    pathsListContainer.appendChild(commentBox);
    pathsListContainer.appendChild(document.createElement("br"));
  });

  const exportButton = document.createElement("button");
  exportButton.textContent = "Export";
  exportButton.id = "export-button";
  pathsListContainer.appendChild(exportButton);

  exportButton.addEventListener("click", function () {
    const pathComments = [];
    document.querySelectorAll(".paths-list label").forEach((label, index) => {
      const path = label.textContent.trim();
      const comment = document
        .querySelectorAll(".comment-box")
        [index].value.trim();
      pathComments.push({ path, comment });
    });

    fetch("/save_paths", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ paths: paths }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          console.log("Paths saved to the database successfully.");
        } else {
          console.error("Error saving paths:", data.message);
        }
      });

    fetch("/export_comments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        comments: pathComments,
        username: '{{ session["username"] }}',
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          alert("Comments exported successfully!");
        } else {
          alert("Failed to export comments.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });

  /* document.querySelectorAll(".path-checkbox").forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
      if (this.checked) {
        uncheckAllExcept(this); // Uncheck other checkboxes
        clearBoxes(); // Clear any previous boxes
        drawBoxesForPath(this.dataset.path); // Draw boxes for the selected path
      } else {
        clearBoxes(); // Clear boxes if unchecked
      }
    });
  }); */

});

function uncheckAllExcept(selectedCheckbox) {
  document.querySelectorAll(".path-checkbox").forEach((checkbox) => {
    if (checkbox !== selectedCheckbox) {
      checkbox.checked = false; // Uncheck other checkboxes
    }
  });
}

/*function drawBoxesForPath(path) {
  clearBoxes();

  fetch("/get_coordinates_for_path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: path }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        data.boxes.forEach((box) => {
          const graphBoxElement = document.createElement("div");
          graphBoxElement.classList.add("draw-box");
          graphBoxElement.style.left = `${box.graph_left}px`;
          graphBoxElement.style.top = `${box.graph_top}px`;
          graphBoxElement.style.width = `${box.graph_width}px`;
          graphBoxElement.style.height = `${box.graph_height}px`;
          graphBoxElement.style.borderColor = "blue";

          document
            .getElementById("graph-container")
            .appendChild(graphBoxElement);

          const codeBoxElement = document.createElement("div");
          codeBoxElement.classList.add("draw-box");
          codeBoxElement.style.left = `${box.code_left}px`;
          codeBoxElement.style.top = `${box.code_top}px`;
          codeBoxElement.style.width = `${box.code_width}px`;
          codeBoxElement.style.height = `${box.code_height}px`;
          codeBoxElement.style.borderColor = "blue";

          document.getElementById("code-container").appendChild(codeBoxElement);
        });
      } else {
        console.error("Error fetching coordinates:", data.message);
      }
    })
    .catch((error) => console.error("Error fetching coordinates:", error));
} */

function clearBoxes() {
  document
    .querySelectorAll("#graph-container .draw-box")
    .forEach((box) => box.remove());
  document
    .querySelectorAll("#code-container .draw-box")
    .forEach((box) => box.remove());
}

function confirmLogout() {
  return confirm("Are you sure you want to log out?");
}

//////////* Eye tracker *//////////

document.getElementById("start-button").addEventListener("click", function () {
  document.getElementById("start-button").style.display = "none";
  // Send a request to start the eye tracker
  fetch("/start_eyetracker", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        console.log("Eye tracker started successfully.");
        showPopupMessage("The eye-tracker has started", 2000); 
        listenForGazeData();
      } else {
        console.error("Error starting eye tracker:", data.message);
      }
    })
    .catch((error) => console.error("Error:", error));
});


function showPopupMessage(message, duration) {
  // Create the pop-up element
  const popup = document.createElement("div");
  popup.textContent = message;
  popup.className = "popup-message";

  document.body.appendChild(popup);

  setTimeout(() => {
    popup.remove();
  }, duration);
}

function getSectionOffsets() {
  // Get the code and graph containers by their IDs
  const codeContainer = document.getElementById("code-container");
  const graphContainer = document.getElementById("graph-container");

  const codeOffset = {
    left: codeContainer.offsetLeft,
    top: codeContainer.offsetTop,
  };

  const graphOffset = {
    left: graphContainer.offsetLeft,
    top: graphContainer.offsetTop,
  };

  console.log("Code Container Offset:", codeOffset);
  console.log("Graph Container Offset:", graphOffset);

  return { code: codeOffset, graph: graphOffset };
}

getSectionOffsets();

//////////*  Red-Boxes *//////////

let gazeDurations = {}; // Tracks gaze duration for each AOI by ID
const timeThreshold = 200; // time Threshold in milliseconds
let lastGazeTimestamp = null;

function drawRedBox(box, type) {
  const containerId = type === "code" ? "code-container" : "graph-container";
  const container = document.getElementById(containerId);

  if (!container) {
    console.error(`Container for type "${type}" not found.`);
    return;
  }

  const containerRect = container.getBoundingClientRect();

  // Create or reuse the red box
  let redBox = document.getElementById(`red-box-${type}`);
  if (!redBox) {
    redBox = document.createElement("div");
    redBox.id = `red-box-${type}`;
    container.appendChild(redBox);
  }

  // Adjust coordinates relative to the container
  redBox.style.left = `${box.box_left - containerRect.left}px`;
  redBox.style.top = `${box.box_top - containerRect.top}px`;
  redBox.style.width = `${box.box_width}px`;
  redBox.style.height = `${box.box_height}px`;

  console.log(`Red box drawn for ${type}:`, {
    left: redBox.style.left,
    top: redBox.style.top,
    width: redBox.style.width,
    height: redBox.style.height,
  });
}

let currentMatchedBoxId = null; // Track the current matched box ID

function drawBoxesForMatchedId(matchedBoxId) {
  fetch(`/get_aoi_by_id?id=${matchedBoxId}`)
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success" && data.aoi) {
        const aoi = data.aoi;

        // Draw the red box for the code container
        if (aoi.code) {
          drawRedBox(aoi.code, "code");
        }

        // Draw the red box for the graph container
        if (aoi.graph) {
          drawRedBox(aoi.graph, "graph");
        }
      } else {
        console.error("Error fetching AOI:", data.message);
      }
    })
    .catch((error) => console.error("Error:", error));
}

function updateGazeDuration(matchedBoxId) {
  const now = Date.now();

  // If gaze is on the same AOI, update the duration
  if (gazeDurations[matchedBoxId]) {
    gazeDurations[matchedBoxId].duration += now - lastGazeTimestamp;
  } else {
    // Initialize gaze duration for this AOI
    gazeDurations[matchedBoxId] = { duration: 0 };
  }

  // Update the last gaze timestamp
  lastGazeTimestamp = now;

  // Check if gaze duration exceeds the threshold
  if (gazeDurations[matchedBoxId].duration >= timeThreshold) {
    drawBoxesForMatchedId(matchedBoxId); 
    delete gazeDurations[matchedBoxId]; 
  }
}

function pollForUpdates() {
  fetch("/get_latest_match") 
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success" && data.match) {
        const latestBoxId = data.match.matched_box_id;

        if (latestBoxId === currentMatchedBoxId) {
          updateGazeDuration(latestBoxId);
        } else {
          gazeDurations = {}; // Clear durations for all AOIs
          currentMatchedBoxId = latestBoxId;
          lastGazeTimestamp = Date.now(); // Start timing for the new AOI
        }
      }
    })
    .catch((error) => console.error("Error polling for updates:", error));
}

// Poll every 200ms for updates
setInterval(pollForUpdates, 200);
