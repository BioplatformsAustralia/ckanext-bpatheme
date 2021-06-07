/*! modernizr 3.6.0 (Custom Build) | MIT *
 * https://modernizr.com/download/?-setclasses-testprop-teststyles !*/
!function (e, n, t) {
  function r(e, n) {
    return typeof e === n
  }

  function o() {
    var e, n, t, o, s, i, l;
    for (var a in h) if (h.hasOwnProperty(a)) {
      if (e = [], n = h[a], n.name && (e.push(n.name.toLowerCase()), n.options && n.options.aliases && n.options.aliases.length)) for (t = 0; t < n.options.aliases.length; t++) e.push(n.options.aliases[t].toLowerCase());
      for (o = r(n.fn, "function") ? n.fn() : n.fn, s = 0; s < e.length; s++) i = e[s], l = i.split("."), 1 === l.length ? Modernizr[l[0]] = o : (!Modernizr[l[0]] || Modernizr[l[0]] instanceof Boolean || (Modernizr[l[0]] = new Boolean(Modernizr[l[0]])), Modernizr[l[0]][l[1]] = o), y.push((o ? "" : "no-") + l.join("-"))
    }
  }

  function s(e) {
    var n = v.className, t = Modernizr._config.classPrefix || "";
    if (C && (n = n.baseVal), Modernizr._config.enableJSClass) {
      var r = new RegExp("(^|\\s)" + t + "no-js(\\s|$)");
      n = n.replace(r, "$1" + t + "js$2")
    }
    Modernizr._config.enableClasses && (n += " " + t + e.join(" " + t), C ? v.className.baseVal = n : v.className = n)
  }

  function i(e, n) {
    return !!~("" + e).indexOf(n)
  }

  function l() {
    return "function" != typeof n.createElement ? n.createElement(arguments[0]) : C ? n.createElementNS.call(n, "http://www.w3.org/2000/svg", arguments[0]) : n.createElement.apply(n, arguments)
  }

  function a(e) {
    return e.replace(/([a-z])-([a-z])/g, function (e, n, t) {
      return n + t.toUpperCase()
    }).replace(/^-/, "")
  }

  function u() {
    var e = n.body;
    return e || (e = l(C ? "svg" : "body"), e.fake = !0), e
  }

  function f(e, t, r, o) {
    var s, i, a, f, d = "modernizr", c = l("div"), p = u();
    if (parseInt(r, 10)) for (; r--;) a = l("div"), a.id = o ? o[r] : d + (r + 1), c.appendChild(a);
    return s = l("style"), s.type = "text/css", s.id = "s" + d, (p.fake ? p : c).appendChild(s), p.appendChild(c), s.styleSheet ? s.styleSheet.cssText = e : s.appendChild(n.createTextNode(e)), c.id = d, p.fake && (p.style.background = "", p.style.overflow = "hidden", f = v.style.overflow, v.style.overflow = "hidden", v.appendChild(p)), i = t(c, e), p.fake ? (p.parentNode.removeChild(p), v.style.overflow = f, v.offsetHeight) : c.parentNode.removeChild(c), !!i
  }

  function d(n, t, r) {
    var o;
    if ("getComputedStyle" in e) {
      o = getComputedStyle.call(e, n, t);
      var s = e.console;
      if (null !== o) r && (o = o.getPropertyValue(r)); else if (s) {
        var i = s.error ? "error" : "log";
        s[i].call(s, "getComputedStyle returning null, its possible modernizr test results are inaccurate")
      }
    } else o = !t && n.currentStyle && n.currentStyle[r];
    return o
  }

  function c(e) {
    return e.replace(/([A-Z])/g, function (e, n) {
      return "-" + n.toLowerCase()
    }).replace(/^ms-/, "-ms-")
  }

  function p(n, r) {
    var o = n.length;
    if ("CSS" in e && "supports" in e.CSS) {
      for (; o--;) if (e.CSS.supports(c(n[o]), r)) return !0;
      return !1
    }
    if ("CSSSupportsRule" in e) {
      for (var s = []; o--;) s.push("(" + c(n[o]) + ":" + r + ")");
      return s = s.join(" or "), f("@supports (" + s + ") { #modernizr { position: absolute; } }", function (e) {
        return "absolute" == d(e, null, "position")
      })
    }
    return t
  }

  function m(e, n, o, s) {
    function u() {
      d && (delete w.style, delete w.modElem)
    }

    if (s = r(s, "undefined") ? !1 : s, !r(o, "undefined")) {
      var f = p(e, o);
      if (!r(f, "undefined")) return f
    }
    for (var d, c, m, y, h, g = ["modernizr", "tspan", "samp"]; !w.style && g.length;) d = !0, w.modElem = l(g.shift()), w.style = w.modElem.style;
    for (m = e.length, c = 0; m > c; c++) if (y = e[c], h = w.style[y], i(y, "-") && (y = a(y)), w.style[y] !== t) {
      if (s || r(o, "undefined")) return u(), "pfx" == n ? y : !0;
      try {
        w.style[y] = o
      } catch (v) {
      }
      if (w.style[y] != h) return u(), "pfx" == n ? y : !0
    }
    return u(), !1
  }

  var y = [], h = [], g = {
    _version: "3.6.0",
    _config: {classPrefix: "", enableClasses: !0, enableJSClass: !0, usePrefixes: !0},
    _q: [],
    on: function (e, n) {
      var t = this;
      setTimeout(function () {
        n(t[e])
      }, 0)
    },
    addTest: function (e, n, t) {
      h.push({name: e, fn: n, options: t})
    },
    addAsyncTest: function (e) {
      h.push({name: null, fn: e})
    }
  }, Modernizr = function () {
  };
  Modernizr.prototype = g, Modernizr = new Modernizr;
  var v = n.documentElement, C = "svg" === v.nodeName.toLowerCase(), S = (g.testStyles = f, {elem: l("modernizr")});
  Modernizr._q.push(function () {
    delete S.elem
  });
  var w = {style: S.elem.style};
  Modernizr._q.unshift(function () {
    delete w.style
  });
  g.testProp = function (e, n, r) {
    return m([e], t, n, r)
  };
  o(), s(y), delete g.addTest, delete g.addAsyncTest;
  for (var _ = 0; _ < Modernizr._q.length; _++) Modernizr._q[_]();
  e.Modernizr = Modernizr
}(window, document);