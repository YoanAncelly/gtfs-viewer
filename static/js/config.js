/**
 * Configuration page JavaScript
 * Handles the configuration interface for GTFS-RT data sources
 */

$(document).ready(() => {
	// Load configuration data when page loads
	loadConfig();

	// Toggle URL inputs based on local files checkbox
	$("#use-local-files").change(function () {
		toggleUrlInputs($(this).is(":checked"));
	});

	$("#edit-use-local-files").change(function () {
		toggleEditUrlInputs($(this).is(":checked"));
	});

	// Add source button click
	$("#add-source-btn").click(() => {
		resetAddSourceForm();
		const addSourceModal = new bootstrap.Modal(
			document.getElementById("add-source-modal"),
		);
		addSourceModal.show();
	});

	// Test URLs button click
	$("#test-urls-btn").click(() => {
		testUrls();
	});

	// Edit test URLs button click
	$("#edit-test-urls-btn").click(() => {
		testEditUrls();
	});

	// Save source button click
	$("#save-source-btn").click(() => {
		saveNewSource();
	});

	// Update source button click
	$("#update-source-btn").click(() => {
		updateSource();
	});

	// Refresh data button click
	$("#refresh-data-btn").click(() => {
		refreshData();
	});
});

/**
 * Load configuration data from the server
 */
function loadConfig() {
	$.ajax({
		url: "/api/config",
		method: "GET",
		dataType: "json",
		success: (response) => {
			renderSources(response);
		},
		error: (xhr, status, error) => {
			showAlert(
				"danger",
				`Erreur lors du chargement de la configuration: ${error}`,
			);
		},
	});
}

/**
 * Render the sources in the UI
 * @param {Object} config - Configuration object
 */
function renderSources(config) {
	const sourcesContainer = $("#sources-container");
	sourcesContainer.empty();

	if (!config || !config.sources || config.sources.length === 0) {
		sourcesContainer.html(
			'<div class="col-12"><div class="alert alert-warning">Aucune source configurée.</div></div>',
		);
		return;
	}

	config.sources.forEach((source, index) => {
		const isActive = index === config.current_source;
		const sourceCard = $(`
            <div class="col-md-6">
                <div class="card source-card ${isActive ? "active-source" : ""}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="card-title mb-0">${source.name}</h5>
                        <div class="btn-group">
                            ${isActive ? '<span class="badge bg-success me-2">Active</span>' : ""}
                            <button class="btn btn-sm btn-outline-primary edit-source" data-index="${index}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger remove-source" data-index="${index}">
                                <i class="fas fa-trash"></i>
                            </button>
                            ${
															!isActive
																? `<button class="btn btn-sm btn-outline-success set-active" data-index="${index}">
                                <i class="fas fa-check"></i>
                            </button>`
																: ""
														}
                        </div>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item">
                                <strong>Type :</strong> ${source.use_local_files ? "Fichiers locaux" : "URLs"}
                            </li>
                            ${
															!source.use_local_files
																? `
                                <li class="list-group-item">
                                    <strong>Trip Update URL :</strong> ${source.trip_update_url || "-"}
                                </li>
                                <li class="list-group-item">
                                    <strong>Vehicle Position URL :</strong> ${source.vehicle_position_url || "-"}
                                </li>
                                <li class="list-group-item">
                                    <strong>Alert URL :</strong> ${source.alert_url || "-"}
                                </li>
                            `
																: ""
														}
                        </ul>
                    </div>
                </div>
            </div>
        `);

		sourcesContainer.append(sourceCard);
	});

	// Add event listeners for source actions
	$(".edit-source").click(function () {
		const index = $(this).data("index");
		editSource(index);
	});

	$(".remove-source").click(function () {
		const index = $(this).data("index");
		confirmRemoveSource(index);
	});

	$(".set-active").click(function () {
		const index = $(this).data("index");
		setActiveSource(index);
	});
}

/**
 * Toggle URL inputs based on local files checkbox
 * @param {boolean} useLocalFiles - Whether to use local files
 */
function toggleUrlInputs(useLocalFiles) {
	if (useLocalFiles) {
		$(".url-input-group").addClass("d-none");
	} else {
		$(".url-input-group").removeClass("d-none");
	}
}

/**
 * Toggle edit URL inputs based on local files checkbox
 * @param {boolean} useLocalFiles - Whether to use local files
 */
function toggleEditUrlInputs(useLocalFiles) {
	if (useLocalFiles) {
		$(".edit-url-input-group").addClass("d-none");
	} else {
		$(".edit-url-input-group").removeClass("d-none");
	}
}

/**
 * Reset the add source form
 */
function resetAddSourceForm() {
	$("#source-name").val("");
	$("#trip-update-url").val("");
	$("#vehicle-position-url").val("");
	$("#alert-url").val("");
	$("#use-local-files").prop("checked", false);
	toggleUrlInputs(false);
	$("#test-results").addClass("d-none").empty();
}

/**
 * Test the URLs in the add source form
 */
function testUrls() {
	const tripUpdateUrl = $("#trip-update-url").val();
	const vehiclePositionUrl = $("#vehicle-position-url").val();
	const alertUrl = $("#alert-url").val();

	// At least one URL must be provided
	if (!tripUpdateUrl && !vehiclePositionUrl && !alertUrl) {
		showAlert("warning", "Veuillez saisir au moins une URL à tester.");
		return;
	}

	// Show loading indicator
	$("#test-results")
		.removeClass("d-none")
		.html(
			'<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div>',
		);

	$.ajax({
		url: "/api/config/test-source",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({
			trip_update_url: tripUpdateUrl,
			vehicle_position_url: vehiclePositionUrl,
			alert_url: alertUrl,
		}),
		dataType: "json",
		success: (response) => {
			displayTestResults(response.results, "#test-results");
		},
		error: (xhr, status, error) => {
			$("#test-results").html(
				`<div class="alert alert-danger">Erreur lors du test: ${error}</div>`,
			);
		},
	});
}

/**
 * Test the URLs in the edit source form
 */
function testEditUrls() {
	const tripUpdateUrl = $("#edit-trip-update-url").val();
	const vehiclePositionUrl = $("#edit-vehicle-position-url").val();
	const alertUrl = $("#edit-alert-url").val();

	// At least one URL must be provided
	if (!tripUpdateUrl && !vehiclePositionUrl && !alertUrl) {
		showAlert("warning", "Veuillez saisir au moins une URL à tester.");
		return;
	}

	// Show loading indicator
	$("#edit-test-results")
		.removeClass("d-none")
		.html(
			'<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div>',
		);

	$.ajax({
		url: "/api/config/test-source",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({
			trip_update_url: tripUpdateUrl,
			vehicle_position_url: vehiclePositionUrl,
			alert_url: alertUrl,
		}),
		dataType: "json",
		success: (response) => {
			displayTestResults(response.results, "#edit-test-results");
		},
		error: (xhr, status, error) => {
			$("#edit-test-results").html(
				`<div class="alert alert-danger">Erreur lors du test: ${error}</div>`,
			);
		},
	});
}

/**
 * Display test results
 * @param {Object} results - Test results
 * @param {string} containerId - Container ID to display results in
 */
function displayTestResults(results, containerId) {
	const container = $(containerId);
	container.empty();

	const resultsList = $('<ul class="list-group"></ul>');

	for (const feedType in results) {
		const result = results[feedType];
		const feedTypeDisplay = {
			trip_update: "TripUpdate",
			vehicle_position: "VehiclePosition",
			alert: "Alert",
		}[feedType];

		let statusClass = "test-neutral";
		let statusIcon = "fa-question-circle";
		let statusMessage = "Statut inconnu";

		if (result.success === true) {
			statusClass = "test-success";
			statusIcon = "fa-check-circle";
			statusMessage = `Code: ${result.status_code} (OK)`;
		} else if (result.success === false) {
			statusClass = "test-error";
			statusIcon = "fa-times-circle";
			statusMessage = result.error
				? `Erreur: ${result.error}`
				: result.status_code
					? `Code: ${result.status_code} (Erreur)`
					: "Échec";
		}

		const listItem = $(`
            <li class="list-group-item test-result-item">
                <div class="d-flex align-items-center">
                    <i class="fas ${statusIcon} ${statusClass} me-2"></i>
                    <div>
                        <strong>${feedTypeDisplay}:</strong> 
                        <span>${statusMessage}</span>
                    </div>
                </div>
            </li>
        `);

		resultsList.append(listItem);
	}

	container.append(resultsList);
}

/**
 * Save a new source
 */
function saveNewSource() {
	// Validate required fields
	const sourceName = $("#source-name").val();
	if (!sourceName) {
		showAlert("warning", "Veuillez saisir un nom pour la source.");
		return;
	}

	const useLocalFiles = $("#use-local-files").is(":checked");
	let tripUpdateUrl = "";
	let vehiclePositionUrl = "";
	let alertUrl = "";

	// If not using local files, at least one URL must be provided
	if (!useLocalFiles) {
		tripUpdateUrl = $("#trip-update-url").val();
		vehiclePositionUrl = $("#vehicle-position-url").val();
		alertUrl = $("#alert-url").val();

		if (!tripUpdateUrl && !vehiclePositionUrl && !alertUrl) {
			showAlert(
				"warning",
				"Veuillez saisir au moins une URL ou utiliser des fichiers locaux.",
			);
			return;
		}
	}

	// Prepare source data
	const source = {
		name: sourceName,
		use_local_files: useLocalFiles,
		trip_update_url: tripUpdateUrl,
		vehicle_position_url: vehiclePositionUrl,
		alert_url: alertUrl,
	};

	// Send request to add source
	$.ajax({
		url: "/api/config/add-source",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify(source),
		dataType: "json",
		success: (response) => {
			if (response.success) {
				// Close modal
				bootstrap.Modal.getInstance(
					document.getElementById("add-source-modal"),
				).hide();
				// Reload config
				loadConfig();
				showAlert("success", "Source ajoutée avec succès.");
			} else {
				showAlert(
					"danger",
					`Erreur lors de l'ajout de la source: ${response.error || "Une erreur inconnue est survenue."}`,
				);
			}
		},
		error: (xhr, status, error) => {
			showAlert("danger", `Erreur lors de l'ajout de la source: ${error}`);
		},
	});
}

/**
 * Edit a source
 * @param {number} index - Source index
 */
function editSource(index) {
	// Load current config
	$.ajax({
		url: "/api/config",
		method: "GET",
		dataType: "json",
		success: (config) => {
			if (!config || !config.sources || !config.sources[index]) {
				showAlert("danger", "Source introuvable.");
				return;
			}

			const source = config.sources[index];

			// Fill edit form
			$("#edit-source-index").val(index);
			$("#edit-source-name").val(source.name);
			$("#edit-trip-update-url").val(source.trip_update_url || "");
			$("#edit-vehicle-position-url").val(source.vehicle_position_url || "");
			$("#edit-alert-url").val(source.alert_url || "");
			$("#edit-use-local-files").prop(
				"checked",
				source.use_local_files || false,
			);
			toggleEditUrlInputs(source.use_local_files || false);
			$("#edit-test-results").addClass("d-none").empty();

			// Show edit modal
			const editSourceModal = new bootstrap.Modal(
				document.getElementById("edit-source-modal"),
			);
			editSourceModal.show();
		},
		error: (xhr, status, error) => {
			showAlert(
				"danger",
				`Erreur lors du chargement de la configuration: ${error}`,
			);
		},
	});
}

/**
 * Update a source
 */
function updateSource() {
	// Get source index
	const index = $("#edit-source-index").val();

	// Validate required fields
	const sourceName = $("#edit-source-name").val();
	if (!sourceName) {
		showAlert("warning", "Veuillez saisir un nom pour la source.");
		return;
	}

	const useLocalFiles = $("#edit-use-local-files").is(":checked");
	let tripUpdateUrl = "";
	let vehiclePositionUrl = "";
	let alertUrl = "";

	// If not using local files, at least one URL must be provided
	if (!useLocalFiles) {
		tripUpdateUrl = $("#edit-trip-update-url").val();
		vehiclePositionUrl = $("#edit-vehicle-position-url").val();
		alertUrl = $("#edit-alert-url").val();

		if (!tripUpdateUrl && !vehiclePositionUrl && !alertUrl) {
			showAlert(
				"warning",
				"Veuillez saisir au moins une URL ou utiliser des fichiers locaux.",
			);
			return;
		}
	}

	// Prepare source data
	const source = {
		name: sourceName,
		use_local_files: useLocalFiles,
		trip_update_url: tripUpdateUrl,
		vehicle_position_url: vehiclePositionUrl,
		alert_url: alertUrl,
	};

	// Send request to update source
	$.ajax({
		url: "/api/config/update-source",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({
			index: Number.parseInt(index),
			source: source,
		}),
		dataType: "json",
		success: (response) => {
			if (response.success) {
				// Close modal
				bootstrap.Modal.getInstance(
					document.getElementById("edit-source-modal"),
				).hide();
				// Reload config
				loadConfig();
				showAlert("success", "Source mise à jour avec succès.");
			} else {
				showAlert(
					"danger",
					`Erreur lors de la mise à jour de la source: ${response.error || "Une erreur inconnue est survenue."}`,
				);
			}
		},
		error: (xhr, status, error) => {
			showAlert(
				"danger",
				`Erreur lors de la mise à jour de la source: ${error}`,
			);
		},
	});
}

/**
 * Confirm removing a source
 * @param {number} index - Source index
 */
function confirmRemoveSource(index) {
	// Set source index in modal
	$("#remove-source-index").val(index);

	// Show confirmation modal
	const confirmModal = new bootstrap.Modal(
		document.getElementById("confirm-remove-modal"),
	);
	confirmModal.show();

	// Set confirm button action
	$("#confirm-remove-btn").one("click", () => {
		removeSource(index);
		confirmModal.hide();
	});
}

/**
 * Remove a source
 * @param {number} index - Source index
 */
function removeSource(index) {
	// Send request to remove source
	$.ajax({
		url: "/api/config/remove-source",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({
			index: Number.parseInt(index),
		}),
		dataType: "json",
		success: (response) => {
			if (response.success) {
				// Reload config
				loadConfig();
				showAlert("success", "Source supprimée avec succès.");
			} else {
				showAlert(
					"danger",
					`Erreur lors de la suppression de la source: ${response.error || "Une erreur inconnue est survenue."}`,
				);
			}
		},
		error: (xhr, status, error) => {
			showAlert(
				"danger",
				`Erreur lors de la suppression de la source: ${error}`,
			);
		},
	});
}

/**
 * Set a source as active
 * @param {number} index - Source index
 */
function setActiveSource(index) {
	// Send request to set active source
	$.ajax({
		url: "/api/config/set-current-source",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({
			index: Number.parseInt(index),
		}),
		dataType: "json",
		success: (response) => {
			if (response.success) {
				// Reload config
				loadConfig();
				showAlert("success", "Source active mise à jour avec succès.");
			} else {
				showAlert(
					"danger",
					`Erreur lors de la mise à jour de la source active: ${response.error || "Une erreur inconnue est survenue."}`,
				);
			}
		},
		error: (xhr, status, error) => {
			showAlert(
				"danger",
				`Erreur lors de la mise à jour de la source active: ${error}`,
			);
		},
	});
}

/**
 * Refresh data from current source
 */
function refreshData() {
	// Show loading overlay
	const overlay = $(
		'<div class="loading-overlay"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div></div>',
	);
	$("body").append(overlay);

	// Send request to refresh data
	$.ajax({
		url: "/api/refresh-data",
		method: "POST",
		contentType: "application/json",
		data: JSON.stringify({}),
		dataType: "json",
		success: (response) => {
			// Remove loading overlay
			$(".loading-overlay").remove();

			if (response.success) {
				showAlert("success", "Données rafraîchies avec succès.");
			} else {
				showAlert(
					"danger",
					`Erreur lors du rafraîchissement des données: ${response.error || "Une erreur inconnue est survenue."}`,
				);
			}
		},
		error: (xhr, status, error) => {
			// Remove loading overlay
			$(".loading-overlay").remove();
			showAlert(
				"danger",
				`Erreur lors du rafraîchissement des données: ${error}`,
			);
		},
	});
}

/**
 * Show an alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {string} message - Alert message
 */
function showAlert(type, message) {
	// Create alert element
	const alert = $(`
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);

	// Add alert to container
	const alertContainer = $("#alert-container");
	alertContainer.append(alert);

	// Auto-dismiss after 5 seconds
	setTimeout(() => {
		alert.alert("close");
	}, 5000);
}
