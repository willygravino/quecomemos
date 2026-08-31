/* QC MENU PRINT SHEET
   Un único controlador para apertura, gestos, selección e impresión.
   Reutiliza QCOverlayUI, igual que Crear plato. */
(function () {
  "use strict";

  const UI = window.QCOverlayUI;
  let lastTrigger = null;
  let observer = null;

  function getSheet() {
    return document.getElementById("menuPrintSheet");
  }

  function getBackdrop() {
    return document.getElementById("menuPrintSheetBackdrop");
  }

  function getBody(sheet) {
    if (!sheet) return null;

    return (
      sheet.querySelector("[data-menu-print-body]") ||
      sheet.querySelector(".menu-print-sheet-body") ||
      sheet.querySelector(".plato-create-sheet-body")
    );
  }

  function syncSharedBodyClass() {
    const anotherSheetOpen = document.querySelector(
      ".plato-create-sheet.is-open"
    );

    if (!anotherSheetOpen) {
      document.body.classList.remove("plato-create-sheet-open");
    }
  }

  function setOpen(sheet, open) {
    if (!sheet) return;

    const backdrop = getBackdrop();

    document.body.classList.toggle("menu-print-sheet-open", open);

    if (open) {
      document.body.classList.add("plato-create-sheet-open");
    }

    sheet.classList.toggle("is-open", open);
    sheet.setAttribute("aria-hidden", open ? "false" : "true");

    if (backdrop) {
      backdrop.classList.toggle("is-open", open);
      backdrop.hidden = !open;
      backdrop.setAttribute("aria-hidden", open ? "false" : "true");
    }

    if (!open) {
      sheet.classList.remove("qc-swipe-dragging");
      sheet.style.removeProperty("--qc-swipe-offset");
      syncSharedBodyClass();

      if (lastTrigger && document.contains(lastTrigger)) {
        try {
          lastTrigger.focus({ preventScroll: true });
        } catch (error) {
          lastTrigger.focus();
        }
      }
    }
  }

  function closeSheet(sheet) {
    setOpen(sheet || getSheet(), false);
  }

  function bindGestures(sheet) {
    if (!sheet) return;

    if (sheet.dataset.qcMenuPrintOverlayBound === "1") {
      return;
    }

    const body = getBody(sheet);

    if (!body) {
      console.warn("menuPrintSheet: no se encontró el body scrollable.");
      return;
    }

    if (!UI) {
      console.warn("menuPrintSheet: QCOverlayUI no está disponible.");
      return;
    }

    sheet.dataset.qcMenuPrintOverlayBound = "1";

    UI.bindSwipeDismiss({
      element: sheet,
      direction: "down",
      threshold: 78,
      maxOffset: Math.min(window.innerHeight * 0.55, 360),
      canStart: function () {
        return body.scrollTop <= 1;
      },
      onDismiss: function () {
        closeSheet(sheet);
      },
    });

    UI.bindWheelDismiss({
      element: sheet,
      direction: "down",
      threshold: 105,
      maxOffset: Math.min(window.innerHeight * 0.55, 360),
      physicalSign: -1,
      canStart: function () {
        return body.scrollTop <= 1;
      },
      onDismiss: function () {
        closeSheet(sheet);
      },
    });
  }

  function initCurrentSheet() {
    bindGestures(getSheet());
  }


  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    return parts.length === 2 ? parts.pop().split(";").shift() : "";
  }

  function selectedDates(sheet) {
    if (!sheet) return [];
    return Array.from(
      sheet.querySelectorAll(".js-menu-print-day:checked")
    ).map(function (input) {
      return input.value;
    }).filter(Boolean);
  }

  function setDeleteConfirmVisible(sheet, visible) {
    if (!sheet) return;
    const confirm = sheet.querySelector("[data-menu-delete-confirm]");
    const prepare = sheet.querySelector("[data-menu-delete-prepare]");
    if (confirm) confirm.classList.toggle("d-none", !visible);
    if (prepare && sheet.dataset.menuActionMode === "delete") {
      prepare.classList.toggle("d-none", visible);
    }
  }

  function updateDeleteControls(sheet) {
    if (!sheet || sheet.dataset.menuActionMode !== "delete") return;
    const dates = selectedDates(sheet);
    const prepare = sheet.querySelector("[data-menu-delete-prepare]");
    const label = sheet.querySelector("[data-menu-delete-prepare-label]");
    if (prepare) prepare.disabled = dates.length === 0;
    if (label) {
      label.textContent = !dates.length
        ? "Elegí días"
        : dates.length === 1
          ? "Eliminar 1 día"
          : `Eliminar ${dates.length} días`;
    }
    setDeleteConfirmVisible(sheet, false);
  }

  function configureActionMode(sheet, mode) {
    if (!sheet) return;

    const isDelete = mode === "delete";
    sheet.dataset.menuActionMode = isDelete ? "delete" : "print";
    sheet.classList.toggle("menu-action-mode-delete", isDelete);

    const title = sheet.querySelector("#menuPrintSheetTitle");
    const note = sheet.querySelector("[data-menu-delete-note]");
    const printAction = sheet.querySelector("[data-menu-print-action]");
    const deletePrepare = sheet.querySelector("[data-menu-delete-prepare]");

    if (title) {
      title.textContent = isDelete
        ? "Eliminar menús programados"
        : "Imprimir menú programado";
    }
    if (note) note.classList.toggle("d-none", !isDelete);
    if (printAction) printAction.classList.toggle("d-none", isDelete);
    if (deletePrepare) deletePrepare.classList.toggle("d-none", !isDelete);

    setDeleteConfirmVisible(sheet, false);

    if (isDelete) {
      setAllDays(sheet, false);

      const activeDate = (
        (window.QCDiaActivo && window.QCDiaActivo.get()) || ""
      );

      if (activeDate) {
        const activeInput = sheet.querySelector(
          `.js-menu-print-day[value="${escapeCssValue(activeDate)}"]`
        );
        if (activeInput) {
          activeInput.checked = true;
          syncDayPreview(activeInput);
        }
      }
      updateDeleteControls(sheet);
    } else {
      setAllDays(sheet, true);
    }
  }

  function prepareDelete(sheet) {
    const dates = selectedDates(sheet);
    if (!dates.length) {
      window.alert("Elegí al menos un día para eliminar.");
      return;
    }

    const text = sheet.querySelector("[data-menu-delete-confirm-text]");
    if (text) {
      text.textContent = dates.length === 1
        ? "¿Eliminar la programación manual de este día? Los hábitos fijos se conservarán."
        : `¿Eliminar la programación manual de ${dates.length} días? Los hábitos fijos se conservarán.`;
    }
    setDeleteConfirmVisible(sheet, true);
  }

  async function deleteSelected(sheet, button) {
    const dates = selectedDates(sheet);
    const url = sheet && sheet.dataset.menuDeleteUrl;
    if (!sheet || !url || !dates.length) return;

    if (button) {
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
    }

    const formData = new FormData();
    dates.forEach(function (date) {
      formData.append("fechas", date);
    });

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        cache: "no-store"
      });

      let data = null;
      try {
        data = await response.json();
      } catch (error) {
        data = null;
      }

      if (!response.ok || !data || data.status !== "ok") {
        throw new Error(
          (data && (data.error || data.message)) ||
          "No se pudieron eliminar los menús seleccionados."
        );
      }

      closeSheet(sheet);

      if (typeof window.refrescarMenuProgramado === "function") {
        await window.refrescarMenuProgramado();
      }
    } catch (error) {
      console.error(error);
      window.alert(error.message || "No se pudieron eliminar los menús.");
    } finally {
      if (button && document.contains(button)) {
        button.disabled = false;
        button.removeAttribute("aria-busy");
      }
    }
  }

  function openSheet(trigger) {
    const sheet = getSheet();
    if (!sheet) return;

    configureActionMode(
      sheet,
      trigger && trigger.matches("[data-menu-delete-sheet-open]")
        ? "delete"
        : "print"
    );

    bindGestures(sheet);
    lastTrigger = trigger || document.activeElement;
    setOpen(sheet, true);

    window.setTimeout(function () {
      const first = sheet.querySelector(
        "[data-menu-print-sheet-close], button, input"
      );

      if (!first) return;

      try {
        first.focus({ preventScroll: true });
      } catch (error) {
        first.focus();
      }
    }, 40);
  }

  function setAllDays(sheet, checked) {
    if (!sheet) return;

    sheet.querySelectorAll(".js-menu-print-day").forEach(function (input) {
      input.checked = checked;
    });

    sheet
      .querySelectorAll(".js-menu-print-preview-day")
      .forEach(function (card) {
        card.classList.toggle("d-none", !checked);
      });
  }

  function escapeCssValue(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(value);
    }

    return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  }

  function syncDayPreview(input) {
    const sheet = input && input.closest("#menuPrintSheet");
    if (!sheet) return;

    const selector =
      '.js-menu-print-preview-day[data-print-date="' +
      escapeCssValue(input.value) +
      '"]';

    const card = sheet.querySelector(selector);

    if (card) {
      card.classList.toggle("d-none", !input.checked);
    }
  }

  function parseLocalDate(iso) {
    const parts = iso.split("-").map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2], 12, 0, 0, 0);
  }

  function mondayKey(iso) {
    const date = parseLocalDate(iso);
    const day = date.getDay();
    const distance = (day + 6) % 7;
    date.setDate(date.getDate() - distance);

    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");

    return y + "-" + m + "-" + d;
  }

  function buildPrintRoot(sheet) {
    const selectedChecks = Array.from(
      sheet.querySelectorAll(".js-menu-print-day:checked")
    );

    if (!selectedChecks.length) {
      window.alert("Elegí al menos un día para imprimir.");
      return null;
    }

    const selectedDates = new Set(
      selectedChecks.map(function (check) {
        return check.value;
      })
    );

    const cards = Array.from(
      sheet.querySelectorAll(".js-menu-print-preview-day")
    ).filter(function (card) {
      return selectedDates.has(card.dataset.printDate);
    });

    if (!cards.length) {
      window.alert("No encontré contenido para los días seleccionados.");
      return null;
    }

    const previous = document.getElementById("menuProgramadoPrintRoot");
    if (previous) previous.remove();

    const printRoot = document.createElement("div");
    printRoot.id = "menuProgramadoPrintRoot";

    const title = document.createElement("div");
    title.className = "qc-print-title";
    title.textContent = "Menú programado";
    printRoot.appendChild(title);

    const weeks = {};

    cards.forEach(function (card) {
      const key = mondayKey(card.dataset.printDate);
      if (!weeks[key]) weeks[key] = [];
      weeks[key].push(card);
    });

    Object.keys(weeks)
      .sort()
      .forEach(function (key) {
        const week = document.createElement("section");
        week.className = "qc-print-week";

        const grid = document.createElement("div");
        grid.className = "qc-print-week-grid";

        weeks[key]
          .sort(function (a, b) {
            return a.dataset.printDate.localeCompare(b.dataset.printDate);
          })
          .forEach(function (card) {
            const clone = card.cloneNode(true);
            clone.classList.remove("d-none");
            grid.appendChild(clone);
          });

        week.appendChild(grid);
        printRoot.appendChild(week);
      });

    return printRoot;
  }

  function printSelected() {
    const sheet = getSheet();
    if (!sheet) return;

    const printRoot = buildPrintRoot(sheet);
    if (!printRoot) return;

    document.body.appendChild(printRoot);
    document.body.classList.add("menu-programado-printing");

    let cleaned = false;

    function cleanup() {
      if (cleaned) return;
      cleaned = true;

      document.body.classList.remove("menu-programado-printing");

      const currentRoot = document.getElementById(
        "menuProgramadoPrintRoot"
      );

      if (currentRoot) currentRoot.remove();

      window.removeEventListener("afterprint", cleanup);
    }

    window.addEventListener("afterprint", cleanup);

    try {
      window.print();
    } finally {
      window.setTimeout(cleanup, 60000);
    }
  }

  document.addEventListener("click", function (event) {
    const opener = event.target.closest?.("[data-menu-print-sheet-open], [data-menu-delete-sheet-open]");

    if (opener) {
      event.preventDefault();
      openSheet(opener);
      return;
    }

    const closeButton = event.target.closest?.(
      "[data-menu-print-sheet-close]"
    );

    if (closeButton && closeButton.closest("#menuPrintSheet")) {
      event.preventDefault();
      closeSheet(closeButton.closest("#menuPrintSheet"));
      return;
    }

    const backdrop = event.target.closest?.("[data-menu-print-backdrop]");

    if (backdrop) {
      event.preventDefault();
      closeSheet(getSheet());
      return;
    }

    const selectAll = event.target.closest?.(
      "[data-menu-print-select-all]"
    );

    if (selectAll) {
      event.preventDefault();
      setAllDays(selectAll.closest("#menuPrintSheet"), true);
      return;
    }

    const selectNone = event.target.closest?.(
      "[data-menu-print-select-none]"
    );

    if (selectNone) {
      event.preventDefault();
      setAllDays(selectNone.closest("#menuPrintSheet"), false);
      return;
    }

    const deletePrepare = event.target.closest?.(
      "[data-menu-delete-prepare]"
    );
    if (deletePrepare && deletePrepare.closest("#menuPrintSheet")) {
      event.preventDefault();
      prepareDelete(deletePrepare.closest("#menuPrintSheet"));
      return;
    }

    const deleteCancelConfirm = event.target.closest?.(
      "[data-menu-delete-cancel-confirm]"
    );
    if (deleteCancelConfirm && deleteCancelConfirm.closest("#menuPrintSheet")) {
      event.preventDefault();
      setDeleteConfirmVisible(
        deleteCancelConfirm.closest("#menuPrintSheet"),
        false
      );
      return;
    }

    const deleteAction = event.target.closest?.(
      "[data-menu-delete-action]"
    );
    if (deleteAction && deleteAction.closest("#menuPrintSheet")) {
      event.preventDefault();
      deleteSelected(deleteAction.closest("#menuPrintSheet"), deleteAction);
      return;
    }

    const printAction = event.target.closest?.(
      "[data-menu-print-action]"
    );

    if (printAction) {
      event.preventDefault();
      printSelected();
    }
  });

  document.addEventListener("change", function (event) {
    const input = event.target.closest?.(".js-menu-print-day");
    if (!input) return;

    syncDayPreview(input);

    const sheet = input.closest("#menuPrintSheet");
    if (sheet && sheet.dataset.menuActionMode === "delete") {
      updateDeleteControls(sheet);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;

    const sheet = getSheet();
    if (!sheet || !sheet.classList.contains("is-open")) return;

    event.preventDefault();
    closeSheet(sheet);
  });

  function observeMenuRefreshes() {
    const host = document.getElementById(
      "contenedor-menu-programado-dias"
    );

    if (!host || !window.MutationObserver || observer) return;

    observer = new MutationObserver(function () {
      initCurrentSheet();
    });

    observer.observe(host, {
      childList: true,
      subtree: true,
    });
  }

  initCurrentSheet();
  observeMenuRefreshes();

  document.addEventListener("DOMContentLoaded", function () {
    initCurrentSheet();
    observeMenuRefreshes();
  });
})();
