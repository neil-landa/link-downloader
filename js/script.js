// Link Downloader - Main JavaScript

///////////////////////////////////////////////////////////
// Set current year
const yearEl = document.querySelector(".year");
const currentYear = new Date().getFullYear();
yearEl.textContent = currentYear;

///////////////////////////////////////////////////////////
// Make mobile navigation work

const btnNavEl = document.querySelector(".btn-mobile-nav");
const headerEl = document.querySelector(".header");

btnNavEl.addEventListener("click", function () {
  headerEl.classList.toggle("nav-open");
});

///////////////////////////////////////////////////////////
// Smooth scrolling animation

const allLinks = document.querySelectorAll("a:link");

allLinks.forEach(function (link) {
  link.addEventListener("click", function (e) {
    e.preventDefault();
    const href = link.getAttribute("href");

    // Scroll back to top
    if (href === "#")
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });

    // Scroll to other links
    if (href !== "#" && href.startsWith("#")) {
      const sectionEl = document.querySelector(href);
      sectionEl.scrollIntoView({ behavior: "smooth" });
    }

    // Close mobile naviagtion
    if (link.classList.contains("main-nav-link"))
      headerEl.classList.toggle("nav-open");
  });
});

///////////////////////////////////////////////////////////
// Sticky navigation

const sectionHeroEl = document.querySelector(".section-hero");

const obs = new IntersectionObserver(
  function (entries) {
    const ent = entries[0];
    console.log(ent);

    if (ent.isIntersecting === false) {
      document.body.classList.add("sticky");
    }

    if (ent.isIntersecting === true) {
      document.body.classList.remove("sticky");
    }
  },
  {
    // In the viewport
    root: null,
    threshold: 0,
    rootMargin: "-80px",
  }
);
obs.observe(sectionHeroEl);

///////////////////////////////////////////////////////////
// Fixing flexbox gap property missing in some Safari versions
function checkFlexGap() {
  var flex = document.createElement("div");
  flex.style.display = "flex";
  flex.style.flexDirection = "column";
  flex.style.rowGap = "1px";

  flex.appendChild(document.createElement("div"));
  flex.appendChild(document.createElement("div"));

  document.body.appendChild(flex);
  var isSupported = flex.scrollHeight === 1;
  flex.parentNode.removeChild(flex);
  console.log(isSupported);

  if (!isSupported) document.body.classList.add("no-flexbox-gap");
}
checkFlexGap();

///////////////////////////////////////////////////////////
// Handle form submission for link downloads

const downloadForm = document.querySelector("#linkDownloadForm");
if (downloadForm) {
  // Function to reset link styling
  function resetLinkStyles() {
    const allInputs = downloadForm.querySelectorAll('input[type="url"]');
    allInputs.forEach((input) => {
      input.classList.remove("invalid-link");
    });
  }

  // Function to mark invalid links
  function markInvalidLinks(invalidLinks) {
    resetLinkStyles();
    const allInputs = downloadForm.querySelectorAll('input[type="url"]');

    invalidLinks.forEach((invalidLink) => {
      allInputs.forEach((input) => {
        if (input.value.trim() === invalidLink.url) {
          input.classList.add("invalid-link");
        }
      });
    });
  }

  downloadForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Get the submit button
    const submitBtn = downloadForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    // Reset styles
    resetLinkStyles();

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = "Validating links...";

    // Create message containers if they don't exist
    let errorDiv = document.querySelector(".error-message");
    let resultsDiv = document.querySelector(".results-message");

    if (!errorDiv) {
      errorDiv = document.createElement("div");
      errorDiv.className = "error-message";
      errorDiv.style.cssText =
        "margin-top: 2rem; padding: 1.6rem; background-color: #fee; border: 2px solid #fcc; border-radius: 9px; color: #c33; display: none;";
      downloadForm.appendChild(errorDiv);
    }

    if (!resultsDiv) {
      resultsDiv = document.createElement("div");
      resultsDiv.className = "results-message";
      resultsDiv.style.cssText =
        "margin-top: 2rem; padding: 1.6rem; background-color: #e8f5e9; border: 2px solid #4caf50; border-radius: 9px; color: #2e7d32; display: none;";
      downloadForm.appendChild(resultsDiv);
    }

    errorDiv.style.display = "none";
    resultsDiv.style.display = "none";

    try {
      // Create FormData from the form
      const formData = new FormData(downloadForm);

      // First, validate links
      submitBtn.textContent = "Validating links...";
      const validateResponse = await fetch("/validate", {
        method: "POST",
        body: formData,
      });

      if (validateResponse.ok) {
        const validationData = await validateResponse.json();

        // Mark invalid links
        if (validationData.invalid && validationData.invalid.length > 0) {
          markInvalidLinks(validationData.invalid);
        }

        // If no valid links, show error and stop
        if (!validationData.valid || validationData.valid.length === 0) {
          const invalidMessages = validationData.invalid.map(
            (item) => `${item.title}: ${item.reason}`
          );
          errorDiv.innerHTML = `<strong>All links were rejected:</strong><br>${invalidMessages.join(
            "<br>"
          )}`;
          errorDiv.style.display = "block";
          submitBtn.textContent = originalText;
          submitBtn.disabled = false;
          return;
        }
      }

      // Proceed with download
      submitBtn.textContent = "Downloading... Please wait";
      const response = await fetch("/download", {
        method: "POST",
        body: formData,
      });

      const contentType = response.headers.get("content-type") || "";

      if (response.ok) {
        if (contentType.includes("application/json")) {
          // Handle JSON response with results
          const data = await response.json();

          if (data.has_file && data.session_id) {
            // Download the file
            const fileResponse = await fetch(
              `/download_file/${data.session_id}`
            );
            if (fileResponse.ok) {
              const blob = await fileResponse.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "link-downloader-files.zip";
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);
            }
          }

          // Show results message
          let resultsHTML = "";

          if (data.successful && data.successful.length > 0) {
            const successfulTitles = data.successful.map((item) => item.title);
            resultsHTML += `<strong>Successfully downloaded:</strong><br>${successfulTitles.join(
              "<br>"
            )}`;
          }

          if (data.rejected && data.rejected.length > 0) {
            const rejectedTitles = data.rejected.map((item) => item.title);
            resultsHTML += `<br><br><strong>Could not download:</strong><br>${rejectedTitles.join(
              "<br>"
            )}`;
          }

          if (resultsHTML) {
            resultsDiv.innerHTML = resultsHTML;
            resultsDiv.style.display = "block";
          }

          // Clear form inputs after successful download
          const allInputs = downloadForm.querySelectorAll('input[type="url"]');
          allInputs.forEach((input) => {
            input.value = "";
            input.classList.remove("invalid-link");
          });

          submitBtn.textContent = "Download Complete!";
          setTimeout(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            resultsDiv.style.display = "none";
          }, 5000);
        } else {
          // Handle direct file download (no rejections)
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "link-downloader-files.zip";
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          // Clear all form inputs after successful download
          const allInputs = downloadForm.querySelectorAll('input[type="url"]');
          allInputs.forEach((input) => {
            input.value = "";
            input.classList.remove("invalid-link");
          });

          submitBtn.textContent = "Download Complete!";
          setTimeout(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
          }, 2000);
        }
      } else {
        // Handle error response
        let errorMessage = "Unknown error occurred";
        try {
          if (contentType.includes("application/json")) {
            const errorData = await response.json();
            errorMessage = errorData.error || errorMessage;
          } else {
            const text = await response.text();
            if (text.includes("error") || text.includes("Error")) {
              errorMessage =
                "Server error occurred. Check server logs for details.";
            } else {
              errorMessage = text.substring(0, 200);
            }
          }
        } catch (parseError) {
          console.error("Error parsing response:", parseError);
          errorMessage = `Server returned error (status ${response.status})`;
        }
        errorDiv.textContent = `Error: ${errorMessage}`;
        errorDiv.style.display = "block";
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    } catch (error) {
      console.error("Download error:", error);
      errorDiv.textContent = `Error: ${
        error.message || "Failed to connect to server"
      }`;
      errorDiv.style.display = "block";
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  });
}

// https://unpkg.com/smoothscroll-polyfill@0.4.4/dist/smoothscroll.min.js

/*
.no-flexbox-gap .main-nav-list li:not(:last-child) {
  margin-right: 4.8rem;
}

.no-flexbox-gap .list-item:not(:last-child) {
  margin-bottom: 1.6rem;
}

.no-flexbox-gap .list-icon:not(:last-child) {
  margin-right: 1.6rem;
}

.no-flexbox-gap .delivered-faces {
  margin-right: 1.6rem;
}

.no-flexbox-gap .meal-attribute:not(:last-child) {
  margin-bottom: 2rem;
}

.no-flexbox-gap .meal-icon {
  margin-right: 1.6rem;
}

.no-flexbox-gap .footer-row div:not(:last-child) {
  margin-right: 6.4rem;
}

.no-flexbox-gap .social-links li:not(:last-child) {
  margin-right: 2.4rem;
}

.no-flexbox-gap .footer-nav li:not(:last-child) {
  margin-bottom: 2.4rem;
}

@media (max-width: 75em) {
  .no-flexbox-gap .main-nav-list li:not(:last-child) {
    margin-right: 3.2rem;
  }
}

@media (max-width: 59em) {
  .no-flexbox-gap .main-nav-list li:not(:last-child) {
    margin-right: 0;
    margin-bottom: 4.8rem;
  }
}
*/
