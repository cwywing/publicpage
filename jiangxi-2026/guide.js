/* 景点解说：<details> 负责展开，本地 mp3 负责播放。同一时间只播一段。 */
(function () {
  var active = null;

  function setState(btn, state) {
    var icon = btn.querySelector(".seg-icon");
    var label = btn.querySelector(".seg-play-label");
    var title = btn.getAttribute("data-title") || "";
    btn.classList.toggle("is-playing", state === "playing");
    btn.disabled = state === "loading";
    btn.dataset.busy = state === "loading" ? "1" : "0";
    btn.setAttribute("aria-pressed", state === "playing" ? "true" : "false");
    if (state === "loading") {
      icon.textContent = "…";
      label.textContent = "加载";
      btn.setAttribute("aria-label", "正在加载：" + title);
    } else if (state === "playing") {
      icon.textContent = "||";
      label.textContent = "暂停";
      btn.setAttribute("aria-label", "暂停：" + title);
    } else if (state === "paused") {
      icon.textContent = "▶";
      label.textContent = "继续";
      btn.setAttribute("aria-label", "继续播放：" + title);
    } else {
      icon.textContent = "▶";
      label.textContent = "播放";
      btn.setAttribute("aria-label", "播放：" + title);
    }
  }

  function stopActive() {
    if (!active) return;
    var audio = active.audio;
    var btn = active.btn;
    var seg = active.seg;
    audio.pause();
    try { audio.currentTime = 0; } catch (e) {}
    seg.classList.remove("is-playing");
    setState(btn, "idle");
    active = null;
  }

  document.querySelectorAll(".guide").forEach(function (spot) {
    var allBtn = spot.querySelector(".guide-all");
    var detailsList = spot.querySelectorAll("details");

    function syncAll() {
      var every = Array.prototype.every.call(detailsList, function (d) { return d.open; });
      allBtn.setAttribute("aria-expanded", every ? "true" : "false");
      allBtn.textContent = every ? "全部收起" : "全部展开";
    }

    allBtn.addEventListener("click", function () {
      var open = allBtn.getAttribute("aria-expanded") !== "true";
      detailsList.forEach(function (d) { d.open = open; });
      syncAll();
    });

    detailsList.forEach(function (d) {
      d.addEventListener("toggle", syncAll);
    });

    spot.querySelectorAll(".seg").forEach(function (seg) {
      var btn = seg.querySelector(".seg-play");
      var audio = seg.querySelector("audio");
      var details = seg.querySelector("details");
      var err = seg.querySelector(".seg-err");

      btn.addEventListener("click", function () {
        if (btn.dataset.busy === "1") return;

        if (active && active.audio === audio && !audio.paused) {
          audio.pause();
          seg.classList.remove("is-playing");
          setState(btn, "paused");
          return;
        }

        if (active && active.audio !== audio) stopActive();

        details.open = true;
        err.hidden = true;
        setState(btn, "loading");
        active = { audio: audio, btn: btn, seg: seg };

        var pending = audio.play();
        if (pending && pending.then) {
          pending.then(function () {
            if (!active || active.audio !== audio) return;
            seg.classList.add("is-playing");
            setState(btn, "playing");
          }).catch(function () {
            if (active && active.audio === audio) active = null;
            seg.classList.remove("is-playing");
            setState(btn, "idle");
            err.hidden = false;
          });
        }
      });

      audio.addEventListener("playing", function () {
        if (!active || active.audio !== audio) return;
        seg.classList.add("is-playing");
        setState(btn, "playing");
      });

      audio.addEventListener("ended", function () {
        seg.classList.remove("is-playing");
        setState(btn, "idle");
        if (active && active.audio === audio) active = null;
      });

      audio.addEventListener("error", function () {
        seg.classList.remove("is-playing");
        setState(btn, "idle");
        err.hidden = false;
        if (active && active.audio === audio) active = null;
      });
    });
  });
})();
