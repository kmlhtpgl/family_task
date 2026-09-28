/* The Board.
 *
 * Two jobs, and the split between them is the whole design:
 *
 *   1. Build the canvas. Markup is created here rather than written in
 *      index.html so the board owns its DOM outright -- there is no Streamlit
 *      element inside this document to inherit from or be restyled around.
 *
 *   2. Speak Streamlit's component protocol directly. There is no injected
 *      `Streamlit` global; that comes from the streamlit-component-lib npm
 *      package, which is not available here. The three messages are posted by
 *      hand:
 *
 *        child -> parent  componentReady     required handshake, apiVersion 1.
 *                       The parent holds the frame at display:none until it
 *                       arrives, so skipping it means an invisible board.
 *                       setComponentValue  the action channel.
 *                       setFrameHeight      size to the host viewport.
 *        parent -> child  render             {args, dfs, disabled, theme}
 *
 * The payload deliberately does NOT come from the render message. A declared
 * component's widget id is derived from its args, so passing the payload as an
 * argument gives the component a new identity on every rerun and the value set
 * on the previous identity is dropped -- the action channel would deliver
 * nothing, forever. Instead the payload is read from a hidden #board-data node
 * in the host document, the same handoff the kiosk runtime already uses for
 * #kiosk-config, and watched with a MutationObserver so new data paints the
 * moment it lands.
 *
 * Selecting a person is local state and never round-trips. Ticking a task sends
 * an intent and waits: no row changes here, because the only thing that may
 * change a task is the server accepting it and the payload saying so on the way
 * back down. tools/spike_check.py drives that round trip in a real browser.
 */
(function () {
  "use strict";

  var DATA_NODE_ID = "board-data";
  var root = document.getElementById("board");
  var announcer = document.getElementById("announcer");
  var svgNS = "http://www.w3.org/2000/svg";

  var state = { payload: null, selected: "everyone", seq: 0 };

  /* How long a task may sit past its date, from the payload. Kept as module
     state because the lock chip needs it and the chip is built deep inside the
     render tree. */
  var cachedOverdueDays = 2;

  /* ── Streamlit protocol ─────────────────────────────────────────────────── */

  function post(message) {
    window.parent.postMessage(
      Object.assign({ isStreamlitMessage: true }, message),
      "*"
    );
  }

  /* Actions carry a monotonic seq. Streamlit holds a widget's value until it
     changes, so Python sees the same action again on the next rerun; the seq is
     how it tells "new" from "already handled". `state.seq` is seeded from
     payload.handled_seq in paint() so a remounted frame starts above what
     Python has already seen rather than back at 1. */
  function send(verb, fields) {
    post({
      type: "streamlit:setComponentValue",
      value: Object.assign({ verb: verb, seq: ++state.seq }, fields || {}),
      dataType: "json",
    });
  }

  function hostDocument() {
    /* Same-origin, so the host's DOM is reachable. This is what lets the frame
       read the payload the way the kiosk frame reads its config. */
    try {
      return window.parent.document;
    } catch (e) {
      return null;
    }
  }

  function readPayload() {
    var doc = hostDocument();
    if (!doc) return null;
    var node = doc.getElementById(DATA_NODE_ID);
    if (!node) return null;
    try {
      return JSON.parse(node.textContent || "null");
    } catch (e) {
      return null;
    }
  }

  /* The host viewport height is NOT the height available to the board: the host
   * renders a compact toolbar above this frame, so a frame sized to the full
   * host height hangs off the bottom of the screen and the host does not scroll
   * to reach it. Measure what is actually left instead.

   * The frame's own offset is independent of the frame's height, so this does
   * not feed back into itself. */
  function availableHeight() {
    try {
      if (window.parent && window.parent !== window) {
        var frame = window.frameElement;
        if (frame && window.parent.innerHeight) {
          var top = frame.getBoundingClientRect().top + (window.parent.scrollY || 0);
          return Math.max(320, Math.round(window.parent.innerHeight - top));
        }
      }
    } catch (e) {
      /* Cross-origin or sandboxed host: our own height is the best we have. */
    }
    return window.innerHeight;
  }

  var lastSettledHeight = 0;

  /* The host finishes laying out its toolbar after this frame first loads, so
   * the first measurement of "space left below the frame" is taken while the
   * frame still sits at the top of the page and comes out about a hundred
   * pixels too tall. Nothing later re-measures it, because the frame's own box
   * never changes again -- so a single sample leaves the bottom of the board
   * hanging off the screen. Re-measure briefly and stop once it stops moving. */
  function settleHeight() {
    var tries = 0;
    (function tick() {
      var h = fillViewport();
      if (h !== lastSettledHeight && ++tries < 12) {
        setTimeout(tick, 50);
        return;
      }
      lastSettledHeight = h;
    })();
  }

  function fillViewport() {
    var h = availableHeight();
    post({ type: "streamlit:setFrameHeight", height: h });
    document.documentElement.style.height = h + "px";
    document.body.style.height = h + "px";
    var board = document.getElementById("board");
    if (board) board.style.height = h + "px";
    return h;
  }

  /* ── Small helpers ──────────────────────────────────────────────────────── */

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function svg(tag, attrs) {
    var node = document.createElementNS(svgNS, tag);
    Object.keys(attrs || {}).forEach(function (k) {
      node.setAttribute(k, attrs[k]);
    });
    return node;
  }

  function announce(text) {
    /* Selection changes are silent visual state, so they are narrated for
       anything not looking at the screen. */
    if (announcer) announcer.textContent = text;
  }

  /* ── The clock ──────────────────────────────────────────────────────────── */

  function startClock(node) {
    function tick() {
      var now = new Date();
      node.textContent = now
        .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    tick();
    /* Aligned to the minute boundary so the displayed minute is never a
       fraction of the way through. */
    var toMinute = (60 - new Date().getSeconds()) * 1000;
    setTimeout(function () {
      tick();
      setInterval(tick, 60_000);
    }, toMinute);
  }

  /* ── Header ─────────────────────────────────────────────────────────────── */

  /* "today" only when the day on screen really is today. The picker moves the
     board through a week, and wording that kept saying "today" reported
     Wednesday's numbers under a date that stayed on the real today. */
  function dayWord(payload) {
    if (payload.is_selected_today) return "today";
    return (payload.selected_label || "").split(" ")[0] || "that day";
  }

  function buildHead(payload) {
    var head = el("header", "head");
    var word = dayWord(payload);

    var when = el("div", "head__when");
    var clock = el("div", "head__clock");
    startClock(clock);
    when.appendChild(clock);
    when.appendChild(el("div", "head__date", payload.today_label));
    head.appendChild(when);

    var right = el("div", "head__arc");
    right.appendChild(buildArc(payload.arc || []));

    var t = payload.totals || {};
    var summary = el("div", "head__summary");
    var done = t.done_today || 0;
    var open = t.open_today || 0;
    summary.appendChild(el("b", null, String(done)));
    summary.appendChild(
      el("span", null, done === 1 ? "task done " + word : "tasks done " + word)
    );
    if (t.overdue) {
      var late = el("span", "is-late", "  ·  " + t.overdue + " past due");
      summary.appendChild(late);
    } else if (!open) {
      summary.appendChild(el("span", null, "  ·  nothing left " + word));
    }
    right.appendChild(summary);

    head.appendChild(right);
    return head;
  }

  /* The arc is a one-week day strip. A shallow curve keeps every cell readable
     from across the room and makes each node tappable. */
  function buildArc(arc) {
    var W = 1000;
    var H = 92;
    var node = svg("svg", {
      class: "arc",
      viewBox: "0 0 " + W + " " + H,
      preserveAspectRatio: "none",
      "aria-hidden": "true",
    });

    var defs = svg("defs");
    var grad = svg("linearGradient", {
      id: "arc-grad",
      x1: "0",
      x2: "1",
      y1: "0",
      y2: "0",
    });
    [
      ["0%", "oklch(0.72 0.19 22)"],
      ["50%", "oklch(0.78 0.16 232)"],
      ["100%", "oklch(0.5 0.02 265)"],
    ].forEach(function (stop) {
      var s = svg("stop", { offset: stop[0] });
      s.setAttribute("stop-color", stop[1]);
      grad.appendChild(s);
    });
    defs.appendChild(grad);
    node.appendChild(defs);

    var n = arc.length;
    var pad = 46;
    var usable = W - pad * 2;
    var step = n > 1 ? usable / (n - 1) : 0;
    /* Control the curve's depth. */
    var lift = 20;

    function pointAt(i) {
      return {
        x: pad + step * i,
        y: 30 + Math.abs(i - (n - 1) / 2) * -lift * 0.18 + lift * 0.55,
      };
    }

    function pathThrough(indices) {
      var d = "";
      indices.forEach(function (i, k) {
        var p = pointAt(i);
        if (k === 0) {
          d += "M " + p.x + " " + p.y;
        } else {
          var prev = pointAt(indices[k - 1]);
          var mid = (prev.x + p.x) / 2;
          d += " C " + mid + " " + prev.y + ", " + mid + " " + p.y + ", " + p.x + " " + p.y;
        }
      });
      return d;
    }

    var all = arc.map(function (_, i) {
      return i;
    });
    node.appendChild(svg("path", { class: "arc__track", d: pathThrough(all) }));

    /* The fill runs from the left edge to today, so a glance at the arc tells
       you how far through the week the colour has got. */
    var todayIndex = all.filter(function (i) {
      return arc[i].is_today;
    })[0];
    if (todayIndex != null && todayIndex > 0) {
      var fill = svg("path", { class: "arc__fill", d: pathThrough(all.slice(0, todayIndex + 1)) });
      node.appendChild(fill);
      var len = fill.getTotalLength();
      fill.style.strokeDasharray = len;
      fill.style.strokeDashoffset = len;
      /* Force layout so the transition has a starting value to animate from. */
      void fill.getBoundingClientRect();
      fill.style.strokeDashoffset = "0";
    }

    arc.forEach(function (day, i) {
      var p = pointAt(i);
      var g = svg("g", {
        class:
          "arc__node" +
          (day.is_today ? " arc__node--today" : "") +
          (!day.total ? " arc__node--empty" : ""),
        transform: "translate(" + p.x + " " + p.y + ")",
      });

      var pct = day.ratio == null ? "–" : Math.round(day.ratio * 100) + "%";
      g.appendChild(
        svg("circle", { class: "arc__disc", r: day.is_today ? 21 : 17 })
      );
      var label = svg("text", { class: "arc__pct", y: 0 });
      label.textContent = pct;
      g.appendChild(label);
      node.appendChild(g);

      var num = svg("text", { class: "arc__num", x: p.x, y: p.y + 40 });
      num.textContent = String(day.day);
      node.appendChild(num);

      var dow = svg("text", { class: "arc__day", x: p.x, y: p.y + 55 });
      dow.textContent = day.relative || day.label;
      node.appendChild(dow);

      g.setAttribute("role", "button");
      g.setAttribute("tabindex", "0");
      g.setAttribute("aria-label", (day.relative || day.label) + " " + day.day);
      g.addEventListener("click", function () {
        send("select_day", { date: day.date });
      });
      g.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          send("select_day", { date: day.date });
        }
      });
    });

    return node;
  }

  /* ── People rail ────────────────────────────────────────────────────────── */

  function face(person, className) {
    var box = el("div", className || "person__face");
    if (person.photo) {
      var img = el("img");
      img.src = person.photo;
      img.alt = "";
      img.loading = "lazy";
      /* A photo that 404s must leave the initials rather than a broken frame. */
      img.addEventListener("error", function () {
        box.textContent = person.initials;
      });
      box.appendChild(img);
    } else {
      box.textContent = person.initials;
    }
    return box;
  }

  function buildRail(payload) {
    var rail = el("nav", "rail");
    rail.setAttribute("aria-label", "People");

    var head = el("div", "rail__head");
    head.appendChild(el("span", null, "People"));
    head.appendChild(el("span", null, String((payload.people || []).length)));
    rail.appendChild(head);

    var list = el("div", "rail__list");
    list.appendChild(personButton(payload, null, "everyone", "Everyone", payload.totals));

    (payload.people || []).forEach(function (person) {
      list.appendChild(personButton(payload, person, person.key));
    });

    rail.appendChild(list);
    return rail;
  }

  function personButton(payload, person, key, fallbackName, totals) {
    var btn = el("button", "person");
    btn.type = "button";
    btn.dataset.key = key;
    if (key === state.selected) btn.setAttribute("aria-current", "true");
    if (person) btn.style.setProperty("--person-accent", person.accent);

    btn.appendChild(person ? face(person) : everyoneMark());

    var body = el("div", "person__body");
    body.appendChild(el("div", "person__name", person ? person.name : fallbackName));

    var meta = el("div", "person__meta");
    if (person) {
      meta.textContent = personDueMeta(person, dayWord(payload));
    } else {
      meta.textContent = (totals.open_today || 0) + " still open " + dayWord(payload);
    }
    body.appendChild(meta);
    btn.appendChild(body);

    var score = el("div", "person__score");
    var points = el("div", "person__points");
    points.appendChild(document.createTextNode(String(person ? person.weekly_points : 0)));
    points.appendChild(el("span", null, "PTS"));
    score.appendChild(points);
    btn.appendChild(score);

    btn.addEventListener("click", function () {
      state.selected = key;
      render();
      announce(
        (person ? person.name : "Everyone") + " selected. " + meta.textContent
      );
    });
    return btn;
  }

  function everyoneMark() {
    var mark = el("div", "person__face");
    mark.textContent = "★";
    mark.style.color = "var(--accent)";
    return mark;
  }

  function personDueMeta(person, word) {
    if (person.overdue) {
      return person.overdue + " past due";
    }
    if (!person.due_today) return "Nothing due " + word;
    return person.due_today + (person.due_today === 1 ? " task " : " tasks ") + word;
  }

  /* ── Stage ──────────────────────────────────────────────────────────────── */

  function buildStage(payload) {
    var stage = el("section", "stage");
    if (state.selected === "everyone") {
      return buildOverview(payload, stage);
    }
    var lane = (payload.lanes || []).filter(function (l) {
      return l.key === state.selected;
    })[0];
    // A person with no lane is a real state, not a crash: show why rather than
    // silently dropping the selection back to everyone.
    if (!lane) {
      stage.appendChild(clearCard("Nothing to show", "This person has no tasks on the board."));
      return stage;
    }
    return buildLane(payload, lane, stage);
  }

  function buildOverview(payload, stage) {
    var lanes = payload.lanes || [];
    var title = el("h1", "stage__title");
    title.appendChild(document.createTextNode("Everyone"));
    title.appendChild(el("small", null, lanes.length + " in the family"));
    stage.appendChild(title);

    if (!lanes.length) {
      stage.appendChild(clearCard("Nobody yet", "Add family members in Admin to see lanes here."));
      return stage;
    }

    var grid = el("div", "overview");
    lanes.forEach(function (lane, i) {
      var person = (payload.people || []).filter(function (p) {
        return p.key === lane.key;
      })[0] || {};
      var card = el("div", "mini rise");
      card.style.animationDelay = i * 55 + "ms";
      card.style.setProperty("--person-accent", person.accent || "var(--accent)");

      var head = el("div", "mini__head");
      head.appendChild(face(person, "mini__face"));
      var names = el("div");
      names.appendChild(el("div", "mini__name", lane.name));
      names.appendChild(
        el(
          "div",
          "mini__meta",
          (person.weekly_points || 0) + " pts this week"
        )
      );
      head.appendChild(names);
      card.appendChild(head);

      var pressing = (lane.counts.overdue || 0) + (lane.counts.today || 0);
      var bar = el("div", "mini__bar");
      var fill = el("div", "mini__fill");
      /* A clear day gets a full bar; a day with work on it starts empty and
         fills as things are ticked. Nothing due at all still shows full, but
         the "Nothing due today" wording on the lane is what carries the
         difference -- a bar alone cannot say "clear" and "finished" apart. */
      fill.style.width = (pressing ? 0 : 100) + "%";
      bar.appendChild(fill);
      card.appendChild(bar);

      var stats = el("div", "mini__stats");
      if (lane.counts.overdue) {
        var late = el("span", "is-late");
        late.appendChild(el("b", null, String(lane.counts.overdue)));
        late.appendChild(document.createTextNode(" past due"));
        stats.appendChild(late);
      }
      var open = el("span");
      open.appendChild(el("b", null, String(lane.counts.today)));
      open.appendChild(document.createTextNode(" " + dayWord(payload)));
      stats.appendChild(open);
      if (lane.counts.later) {
        var later = el("span");
        later.appendChild(el("b", null, String(lane.counts.later)));
        later.appendChild(document.createTextNode(" coming"));
        stats.appendChild(later);
      }
      card.appendChild(stats);
      grid.appendChild(card);
    });

    stage.appendChild(grid);
    return stage;
  }

  function buildLane(payload, lane, stage) {
    var person = (payload.people || []).filter(function (p) {
      return p.key === lane.key;
    })[0] || {};
    var counts = lane.counts || {};

    var title = el("h1", "stage__title");
    title.appendChild(document.createTextNode(lane.name));
    title.appendChild(
      el("small", null, (person.weekly_points || 0) + " points this week")
    );
    stage.appendChild(title);

    if (!lane.groups || !lane.groups.length) {
      stage.appendChild(
        clearCard(
          "Nothing due " + dayWord(payload),
          counts.later
            ? counts.later +
              " coming up" +
              (counts.later === 1 ? "" : "s") +
              "."
            : "Enjoy it."
        )
      );
      return stage;
    }

    var groups = el("div", "groups");
    lane.groups.forEach(function (group) {
      groups.appendChild(buildGroup(group));
    });
    stage.appendChild(groups);

    /* Recurring chores are generated months ahead, so this is usually a large
       number. It gets one line rather than a list: it is bookkeeping, not
       something anybody decided to do today. */
    if (lane.scheduled) {
      var ahead = el("div", "scheduled");
      ahead.appendChild(
        el("b", null, lane.scheduled + " scheduled further out")
      );
      ahead.appendChild(
        el("small", null, "recurring chores already generated")
      );
      stage.appendChild(ahead);
    }
    return stage;
  }

  function clearCard(title, detail) {
    var card = el("div", "clear rise");
    card.appendChild(el("div", "clear__mark", "✓"));
    var text = el("div", "clear__text", title);
    text.appendChild(el("small", null, detail));
    card.appendChild(text);
    return card;
  }

  function buildGroup(group) {
    var node = el("div", "group" + (group.tone ? " group--" + group.tone : ""));
    var label = el("div", "group__label");
    label.appendChild(el("div", "group__name", group.name));
    /* The count is the real total, not what fits on screen, so the board never
       implies there is less left than there is. */
    label.appendChild(
      el(
        "div",
        "group__count",
        group.total + (group.total === 1 ? " task" : " tasks")
      )
    );
    node.appendChild(label);

    var items = el("div", "group__items");
    group.tasks.forEach(function (task, i) {
      items.appendChild(buildTask(task, i));
    });

    if (group.hidden) {
      var more = el("div", "more");
      more.appendChild(
        el("span", null, "+" + group.hidden + " more " + group.name.toLowerCase())
      );
      more.appendChild(
        el("small", null, "shown in the classic app")
      );
      items.appendChild(more);
    }

    node.appendChild(items);
    return node;
  }

  function buildTask(task, i) {
    var row = el("div", "task rise");
    row.style.animationDelay = Math.min(i, 6) * 40 + "ms";
    if (task.lock) row.classList.add("task--locked");
    if (task.effective_points < (task.points || 0)) {
      row.classList.add("task--worthless");
    }

    /* The verb comes from the payload, not from the row's own status: the
       canvas cannot be trusted to work out whether a click means "do this" or
       "undo this", and getting it wrong would file somebody's points under the
       wrong task. A locked task is not clickable at all, so the wall board
       cannot collect refusals. */
    if (task.action) {
      row.classList.add("task--live");
      row.setAttribute("role", "button");
      row.setAttribute("tabindex", "0");
      row.setAttribute(
        "aria-label",
        task.action === "reopen"
          ? "Reopen " + task.title
          : "Complete " + task.title + ", " + task.effective_points + " points"
      );
      row.addEventListener("click", function () {
        send(task.action, { task_id: task.id });
      });
      row.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          send(task.action, { task_id: task.id });
        }
      });
    }

    if (task.action) {
      var tick = el(
        "span",
        "task__tick" + (task.action === "reopen" ? " task__tick--reopen" : "")
      );
      row.appendChild(tick);
    }

    row.appendChild(el("div", "task__title", task.title));

    if (task.lock) {
      var chip = el(
        "span",
        "task__lock task__lock--" + task.lock,
        task.lock === "overdue" ? "Past due" : "Not yet"
      );
      /* Spelled out rather than merely greyed, so a locked task explains
         itself instead of looking broken. The window comes from Python, so the
         label cannot drift from the rule that locked the task. */
      chip.title =
        task.lock === "overdue"
          ? "More than " + cachedOverdueDays + " days past its date"
          : "Due later than today";
      row.appendChild(chip);
    }

    var points = el("div", "task__points");
    points.appendChild(document.createTextNode(String(task.effective_points)));
    points.appendChild(el("span", null, "PTS"));
    row.appendChild(points);

    return row;
  }

  /* ── Render ─────────────────────────────────────────────────────────────── */

  var lastJson = null;

  function render() {
    var payload = state.payload;
    if (!payload) return;

    fillViewport();
    root.setAttribute("aria-busy", "false");

    var next = document.createDocumentFragment();
    next.appendChild(buildHead(payload));
    next.appendChild(buildRail(payload));
    next.appendChild(buildStage(payload));
    /* A row is not allowed to tick itself, so the confirmation that the server
       accepted it arrives here instead -- and only for the one render that
       carries it. */
    if (payload.flash) next.appendChild(buildFlash(payload.flash));

    root.textContent = "";
    root.appendChild(next);

    cachedOverdueDays = payload.overdue_days || 2;
  }

  function buildFlash(flash) {
    var toast = el("div", "flash" + (flash.ok ? "" : " flash--bad"), flash.message);
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    /* Removed on a timer as well as by the next repaint: the repaint may be a
       while away, and a message that outlives the task it describes is worse
       than no message. */
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 4200);
    return toast;
  }

  function paint() {
    var payload = readPayload();
    if (payload === null) return;

    /* Resume the action count rather than restarting it. The seq is the frame's
       only "this is new" signal, and it lives in the frame's memory, so a
       remounted frame -- leaving the board for another page and coming back --
       began again at 1 while Python still remembered handling 3. Every click up
       to that number was then discarded as a replay, which is why the day picker
       looked dead until the page was refreshed. Python sends the count it has
       reached, so the frame continues above it. */
    var floor = payload.handled_seq;
    if (typeof floor === "number" && floor > state.seq) state.seq = floor;

    cachedOverdueDays = payload.overdue_days || 2;

    var json = JSON.stringify(payload);
    if (json === lastJson && state.payload) {
      /* Same data: a click should not rebuild the DOM, or a selection would be
         lost and the entrance animation would replay on every rerun. */
      return;
    }
    lastJson = json;
    state.payload = payload;

    /* A person can be deleted while the board is on the wall. */
    if (state.selected !== "everyone") {
      var id = Number(state.selected.split(":")[1]);
      var stillThere = (payload.people || []).some(function (p) {
        return p.id === id;
      });
      if (!stillThere) state.selected = "everyone";
    }

    render();
  }

  function watch() {
    var doc = hostDocument();
    if (!doc || !doc.body || typeof MutationObserver === "undefined") return;

    function attach() {
      var target = doc.getElementById(DATA_NODE_ID);
      if (!target) {
        /* Streamlit replaces the node each run rather than mutating it, so an
           observer attached to the old one would go deaf. Retry briefly, then
           fall back to polling. */
        if (attach.tries < 40) {
          attach.tries = (attach.tries || 0) + 1;
          setTimeout(attach, 100);
          return;
        }
        setInterval(paint, 1000);
        return;
      }
      new MutationObserver(paint).observe(target, {
        childList: true,
        characterData: true,
        subtree: true,
      });
    }

    attach();

    /* The node can be swapped between runs, so re-arm after any removal. */
    doc.addEventListener("DOMNodeRemoved", function (event) {
      if (event.target && event.target.id === DATA_NODE_ID) setTimeout(attach, 60);
    });
  }

  /* ── Keyboard ─────────────────────────────────────────────────────────────
     A wall tablet has no keyboard, but this same board gets opened on a laptop
     and reaching every child with Tab through a wall-sized board is not
     navigation. */
  function bindKeys() {
    document.addEventListener("keydown", function (event) {
      if (!state.payload) return;
      var keys = ["everyone"].concat(
        (state.payload.people || []).map(function (p) {
          return p.key;
        })
      );
      var at = keys.indexOf(state.selected);
      if (event.key === "ArrowDown" || event.key === "ArrowRight") {
        state.selected = keys[(at + 1) % keys.length];
      } else if (event.key === "ArrowUp" || event.key === "ArrowLeft") {
        state.selected = keys[(at - 1 + keys.length) % keys.length];
      } else if (event.key === "Home") {
        state.selected = "everyone";
      } else {
        return;
      }
      event.preventDefault();
      render();
      var active = document.querySelector('.person[aria-current="true"]');
      if (active) active.focus();
    });
  }

  /* ── Boot ───────────────────────────────────────────────────────────────── */

  window.addEventListener("message", function (event) {
    if (event.data && event.data.type === "streamlit:render") paint();
  });

  window.addEventListener("resize", function () {
    settleHeight();
  });

  /* Ready first, size second: Streamlit drops a setFrameHeight that arrives
   * before the handshake. */
  post({ type: "streamlit:componentReady", apiVersion: 1 });
  fillViewport();

  paint();
  settleHeight();
  watch();
  bindKeys();

  /* Exposed for tools/shoot.py and tools/audit.py, which need to reach the
     built canvas and the current selection without scraping markup. */
  window.__board = {
    state: state,
    render: render,
    paint: paint,
    send: send,
  };
})();
