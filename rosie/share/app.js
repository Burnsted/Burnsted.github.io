(function () {
  "use strict";

  var FRIEND_URL = "https://burnsted.github.io/rosie/";
  var SHARE_TITLE = "Meet Rosie";
  var SHARE_TEXT =
    "Here's the Rosie helper I told you about. It reads itself out loud and shows how to get set up.";
  var MESSAGE = SHARE_TEXT + "\n\n" + FRIEND_URL;

  var linkEl = document.getElementById("friend-link");
  var messageEl = document.getElementById("share-message");
  var copyLinkBtn = document.getElementById("btn-copy-link");
  var shareBtn = document.getElementById("btn-share");
  var copyMessageBtn = document.getElementById("btn-copy-message");
  var linkStatus = document.getElementById("link-status");
  var messageStatus = document.getElementById("message-status");

  messageEl.value = MESSAGE;

  function flash(el, text) {
    el.textContent = text;
    window.setTimeout(function () {
      if (el.textContent === text) el.textContent = "";
    }, 2500);
  }

  function copyText(text, statusEl, okMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(
        function () {
          flash(statusEl, okMsg);
        },
        function () {
          fallbackCopy(text, statusEl, okMsg);
        }
      );
    }
    fallbackCopy(text, statusEl, okMsg);
  }

  function fallbackCopy(text, statusEl, okMsg) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, ta.value.length);
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (e) {
      ok = false;
    }
    document.body.removeChild(ta);
    if (ok) {
      flash(statusEl, okMsg);
    } else {
      // Last resort: select the visible friend link / message
      if (statusEl === linkStatus) {
        var range = document.createRange();
        range.selectNodeContents(linkEl);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        flash(statusEl, "Link selected — press Copy on your phone.");
      } else {
        messageEl.focus();
        messageEl.select();
        flash(statusEl, "Message selected — press Copy on your phone.");
      }
    }
  }

  copyLinkBtn.addEventListener("click", function () {
    copyText(FRIEND_URL, linkStatus, "Link copied.");
  });

  copyMessageBtn.addEventListener("click", function () {
    copyText(MESSAGE, messageStatus, "Message copied.");
  });

  if (navigator.share) {
    shareBtn.hidden = false;
    shareBtn.addEventListener("click", function () {
      navigator
        .share({
          title: SHARE_TITLE,
          text: SHARE_TEXT,
          url: FRIEND_URL,
        })
        .then(function () {
          flash(linkStatus, "Shared.");
        })
        .catch(function () {
          // User canceled or share failed — stay quiet
        });
    });
  }
})();
