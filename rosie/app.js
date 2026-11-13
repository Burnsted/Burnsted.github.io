(function () {
  "use strict";

  var SECTIONS = [
    {
      id: "intro",
      audio: "audio/intro.mp3",
      text:
        "Welcome. This page is about Rosie — a companion you talk to out loud. " +
        "You can pause anytime and come back later. " +
        "Use the buttons above to play, pause, go back fifteen seconds, or start over. " +
        "Or tap Listen on any section to hear just that part. " +
        "This page explains what Rosie is, who helps behind her, how your privacy is handled, what you need, and how to begin."
    },
    {
      id: "meet",
      audio: "audio/meet.mp3",
      text:
        "Meet Rosie. Rosie is a companion you talk to out loud — like a patient friend who remembers you. " +
        "She is different from ChatGPT in a few ways. " +
        "She remembers your people, your pill schedule, your lists, and what you like, from one day to the next. " +
        "She has quiet helpers behind her for specific jobs. " +
        "She can check suspicious calls, emails, and texts for scams. " +
        "She can keep reminders. And if you say yes, she can use your email and calendar. " +
        "She goes one step at a time, and she waits for you."
    },
    {
      id: "who",
      audio: "audio/who.mp3",
      text:
        "Who helps. Rosie is the everyday voice you talk with. " +
        "Aunt Patience is her second voice — a calm Southern auntie for sticky problems: " +
        "scam checks, phone and app setup, billing disputes, paperwork follow-through, " +
        "and car questions with her quiet car expert, Miss Daisy. " +
        "Alfred helps with home, meals, groceries, and outings. " +
        "Dolly helps with bills, budgets, spreadsheets, and getting tax papers organized for your preparer. " +
        "Doc helps with health notes, pill lists, refills, and questions for your doctor. " +
        "Doc never replaces your doctor. In an emergency, she says call nine one one. " +
        "Joy brings music, games, trivia, Did You Know stories, and help with TV and movies. " +
        "Keepsake helps with life stories, family, photos, and letters."
    },
    {
      id: "privacy",
      audio: "audio/privacy.mp3",
      text:
        "Your privacy. Rosie never asks for passwords, PINs, or full account numbers. " +
        "She never moves money. " +
        "And she always reads back what she plans to do, then waits for your yes, before sending or scheduling anything."
    },
    {
      id: "need",
      audio: "audio/need.mp3",
      text:
        "What you need. You need a paid plan that includes Grok Bot. " +
        "The Premium plan is thirty dollars a month and includes Grok Bot. Higher plans include it too. " +
        "You also need the Grok Bot app. It runs on iPhone, iPad, Android phones, Mac, Windows, and Linux computers. " +
        "On a phone or tablet, get it from the App Store or Google Play. On a computer, download it from x dot A I slash bot."
    },
    {
      id: "start",
      audio: "audio/start.mp3",
      text:
        "Getting started. One. Choose the Premium plan — or another plan that includes Grok Bot. " +
        "Two. Download the Grok Bot app and sign in. " +
        "Three. Open the Rosie link your friend shares. Use the button below when it is ready. " +
        "Four. Add Rosie as a new bot. " +
        "Five. Tap the voice button and say hello. " +
        "Six. Rosie asks a few easy questions, one at a time, to get to know you. You can skip any, or stop anytime."
    },
    {
      id: "open",
      audio: "audio/open.mp3",
      text:
        "When you’re ready, say: Hi Rosie, let’s get started. And she’ll take it from there."
    }
  ];

  var playBtn = document.getElementById("btn-play");
  var pauseBtn = document.getElementById("btn-pause");
  var backBtn = document.getElementById("btn-back");
  var restartBtn = document.getElementById("btn-restart");
  var statusEl = document.getElementById("status");
  var progressBar = document.getElementById("progress-bar");
  var ctaBox = document.getElementById("rosie-cta");

  var audioEls = [];
  var mode = "idle"; // idle | mp3 | speech
  var playing = false;
  var currentIndex = 0;
  var sectionOnly = false;
  var speechUtterance = null;
  var speechIndex = 0;
  var speechOffset = 0;
  var speechStartStamp = 0;
  var speechPausedAt = 0;
  var preferSpeech = false;
  var durations = [];
  var totalDuration = 0;
  var tickTimer = null;

  function setStatus(msg) {
    statusEl.textContent = msg;
  }

  function setPlayingUi(isPlaying) {
    playing = isPlaying;
    pauseBtn.disabled = !isPlaying;
    playBtn.disabled = isPlaying;
    playBtn.setAttribute("aria-pressed", isPlaying ? "true" : "false");
    if (isPlaying) {
      playBtn.textContent = "Playing…";
    } else if (mode !== "idle" || currentIndex > 0 || speechPausedAt > 0) {
      playBtn.textContent = "Resume";
    } else {
      playBtn.textContent = "Listen";
    }
  }

  function scrollToSection(id) {
    var el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function updateProgress() {
    var elapsed = getElapsed();
    var pct = totalDuration > 0 ? Math.min(100, (elapsed / totalDuration) * 100) : 0;
    progressBar.style.width = pct.toFixed(2) + "%";
  }

  function getElapsed() {
    if (mode === "mp3") {
      var sum = 0;
      for (var i = 0; i < currentIndex; i++) {
        sum += durations[i] || 0;
      }
      var a = audioEls[currentIndex];
      if (a && !isNaN(a.currentTime)) sum += a.currentTime;
      return sum;
    }
    if (mode === "speech") {
      var base = 0;
      for (var j = 0; j < speechIndex; j++) {
        base += estimateSpeechDuration(SECTIONS[j].text);
      }
      if (playing) {
        return base + speechOffset + (performance.now() - speechStartStamp) / 1000;
      }
      return base + speechPausedAt;
    }
    return 0;
  }

  function estimateSpeechDuration(text) {
    // ~130 wpm at rate 0.85 ≈ spoken pace for fallback estimate
    var words = text.trim().split(/\s+/).length;
    return Math.max(2, (words / 130) * 60);
  }

  function stopSpeech() {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    speechUtterance = null;
  }

  function stopAllMp3() {
    audioEls.forEach(function (a) {
      a.pause();
    });
  }

  function clearTick() {
    if (tickTimer) {
      clearInterval(tickTimer);
      tickTimer = null;
    }
  }

  function startTick() {
    clearTick();
    tickTimer = setInterval(updateProgress, 250);
  }

  function finishAll() {
    clearTick();
    mode = "idle";
    currentIndex = 0;
    sectionOnly = false;
    speechIndex = 0;
    speechOffset = 0;
    speechPausedAt = 0;
    setPlayingUi(false);
    playBtn.textContent = "Listen";
    setStatus("Finished. Tap Listen to hear it again.");
    progressBar.style.width = "100%";
  }

  function playMp3From(index, onlyOne) {
    stopSpeech();
    stopAllMp3();
    mode = "mp3";
    sectionOnly = !!onlyOne;
    currentIndex = index;
    var a = audioEls[index];
    if (!a) {
      fallbackToSpeech(index, onlyOne);
      return;
    }
    scrollToSection(SECTIONS[index].id);
    setStatus("Playing…");
    setPlayingUi(true);
    startTick();
    var p = a.play();
    if (p && typeof p.catch === "function") {
      p.catch(function () {
        fallbackToSpeech(index, onlyOne);
      });
    }
  }

  function onMp3Ended(index) {
    if (sectionOnly) {
      finishAll();
      return;
    }
    var next = index + 1;
    if (next >= SECTIONS.length) {
      finishAll();
      return;
    }
    playMp3From(next, false);
  }

  function fallbackToSpeech(index, onlyOne) {
    preferSpeech = true;
    stopAllMp3();
    mode = "speech";
    sectionOnly = !!onlyOne;
    speechIndex = index;
    speechOffset = 0;
    speechPausedAt = 0;
    setStatus("Playing with your phone’s voice…");
    speakFrom(index, 0);
  }

  function speakFrom(index, offsetSec) {
    if (!window.speechSynthesis) {
      setStatus("Audio is not available on this device.");
      setPlayingUi(false);
      return;
    }
    stopSpeech();
    speechIndex = index;
    speechOffset = offsetSec || 0;
    var full = SECTIONS[index].text;
    var text = full;
    if (speechOffset > 0) {
      var approxChars = Math.min(full.length - 1, Math.floor((speechOffset / estimateSpeechDuration(full)) * full.length));
      var cut = full.indexOf(" ", approxChars);
      if (cut < 0) cut = approxChars;
      text = full.slice(cut).trim() || full;
    }
    speechUtterance = new SpeechSynthesisUtterance(text);
    speechUtterance.rate = 0.85;
    speechUtterance.pitch = 1;
    speechUtterance.lang = "en-US";
    var voices = window.speechSynthesis.getVoices();
    var preferred = voices.find(function (v) {
      return /en-US/i.test(v.lang) && /female|Samantha|Karen|Moira|Google US English/i.test(v.name);
    }) || voices.find(function (v) {
      return /en-US/i.test(v.lang);
    });
    if (preferred) speechUtterance.voice = preferred;

    speechUtterance.onstart = function () {
      speechStartStamp = performance.now();
      setPlayingUi(true);
      startTick();
      scrollToSection(SECTIONS[index].id);
    };
    speechUtterance.onend = function () {
      if (sectionOnly) {
        finishAll();
        return;
      }
      var next = index + 1;
      if (next >= SECTIONS.length) {
        finishAll();
        return;
      }
      speechOffset = 0;
      speechPausedAt = 0;
      speakFrom(next, 0);
    };
    speechUtterance.onerror = function () {
      setStatus("Could not play audio. Please try again.");
      setPlayingUi(false);
      clearTick();
    };
    window.speechSynthesis.speak(speechUtterance);
  }

  function pauseAll() {
    if (!playing) return;
    if (mode === "mp3") {
      var a = audioEls[currentIndex];
      if (a) a.pause();
    } else if (mode === "speech") {
      speechPausedAt = speechOffset + (performance.now() - speechStartStamp) / 1000;
      stopSpeech();
    }
    setPlayingUi(false);
    setStatus("Paused. Tap Resume when you are ready.");
    clearTick();
    updateProgress();
  }

  function resumeOrStart() {
    if (playing) return;
    if (mode === "mp3" && audioEls[currentIndex]) {
      setStatus("Playing…");
      setPlayingUi(true);
      startTick();
      audioEls[currentIndex].play().catch(function () {
        fallbackToSpeech(currentIndex, sectionOnly);
      });
      return;
    }
    if (mode === "speech") {
      speakFrom(speechIndex, speechPausedAt || 0);
      return;
    }
    // fresh start
    progressBar.style.width = "0%";
    if (preferSpeech) {
      fallbackToSpeech(0, false);
    } else {
      playMp3From(0, false);
    }
  }

  function restart() {
    stopSpeech();
    stopAllMp3();
    audioEls.forEach(function (a) {
      try { a.currentTime = 0; } catch (e) {}
    });
    currentIndex = 0;
    speechIndex = 0;
    speechOffset = 0;
    speechPausedAt = 0;
    sectionOnly = false;
    mode = "idle";
    progressBar.style.width = "0%";
    setPlayingUi(false);
    playBtn.textContent = "Listen";
    setStatus("Starting from the beginning…");
    if (preferSpeech) {
      fallbackToSpeech(0, false);
    } else {
      playMp3From(0, false);
    }
  }

  function backFifteen() {
    if (mode === "mp3") {
      var a = audioEls[currentIndex];
      if (!a) return;
      var t = a.currentTime - 15;
      if (t >= 0) {
        a.currentTime = t;
      } else {
        var need = Math.abs(t);
        var idx = currentIndex;
        while (idx > 0 && need > 0) {
          idx -= 1;
          var d = durations[idx] || 0;
          if (need <= d) {
            currentIndex = idx;
            stopAllMp3();
            audioEls[idx].currentTime = Math.max(0, d - need);
            if (playing) {
              audioEls[idx].play();
              scrollToSection(SECTIONS[idx].id);
            }
            need = 0;
          } else {
            need -= d;
          }
        }
        if (need > 0) {
          currentIndex = 0;
          audioEls[0].currentTime = 0;
          if (playing) {
            stopAllMp3();
            audioEls[0].play();
            scrollToSection(SECTIONS[0].id);
          }
        }
      }
      updateProgress();
      return;
    }
    if (mode === "speech") {
      var wasPlaying = playing;
      var pos = (playing ? speechOffset + (performance.now() - speechStartStamp) / 1000 : speechPausedAt) - 15;
      stopSpeech();
      if (pos < 0 && speechIndex > 0) {
        var prev = speechIndex - 1;
        var prevDur = estimateSpeechDuration(SECTIONS[prev].text);
        speechIndex = prev;
        speechPausedAt = Math.max(0, prevDur + pos);
      } else {
        speechPausedAt = Math.max(0, pos);
      }
      speechOffset = speechPausedAt;
      if (wasPlaying) {
        speakFrom(speechIndex, speechPausedAt);
      } else {
        updateProgress();
      }
    }
  }

  function setupCta() {
    var link = (typeof window.ROSIE_LINK === "string" && window.ROSIE_LINK.trim()) || "";
    ctaBox.innerHTML = "";
    if (link) {
      var a = document.createElement("a");
      a.className = "btn btn-primary btn-large";
      a.href = link;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "Open Rosie";
      ctaBox.appendChild(a);
    } else {
      var p = document.createElement("p");
      p.className = "cta-note";
      p.textContent = "Ask your friend to text you the Rosie link.";
      ctaBox.appendChild(p);
    }
  }

  function preloadAudio() {
    var pending = SECTIONS.length;
    var failed = 0;
    SECTIONS.forEach(function (sec, i) {
      var a = new Audio();
      a.preload = "auto";
      a.src = sec.audio;
      a.addEventListener("loadedmetadata", function () {
        durations[i] = a.duration || estimateSpeechDuration(sec.text);
        totalDuration = durations.reduce(function (s, d) { return s + (d || 0); }, 0);
        pending -= 1;
        if (pending === 0 && failed === SECTIONS.length) {
          preferSpeech = true;
        }
      });
      a.addEventListener("error", function () {
        failed += 1;
        durations[i] = estimateSpeechDuration(sec.text);
        totalDuration = durations.reduce(function (s, d) { return s + (d || 0); }, 0);
        pending -= 1;
        if (failed === SECTIONS.length) {
          preferSpeech = true;
          setStatus("Ready when you are. (Using your phone’s voice.)");
        }
      });
      a.addEventListener("ended", function () {
        onMp3Ended(i);
      });
      a.addEventListener("timeupdate", updateProgress);
      audioEls[i] = a;
    });
  }

  playBtn.addEventListener("click", resumeOrStart);
  pauseBtn.addEventListener("click", pauseAll);
  backBtn.addEventListener("click", backFifteen);
  restartBtn.addEventListener("click", restart);

  document.querySelectorAll("[data-play-section]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-play-section");
      var idx = SECTIONS.findIndex(function (s) { return s.id === id; });
      if (idx < 0) return;
      stopSpeech();
      stopAllMp3();
      audioEls.forEach(function (a) {
        try { a.currentTime = 0; } catch (e) {}
      });
      progressBar.style.width = "0%";
      if (preferSpeech) {
        fallbackToSpeech(idx, true);
      } else {
        playMp3From(idx, true);
      }
    });
  });

  if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = function () {
      window.speechSynthesis.getVoices();
    };
  }

  setupCta();
  preloadAudio();
})();
