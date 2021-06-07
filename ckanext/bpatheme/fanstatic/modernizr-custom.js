/*! modernizr 3.6.0 (Custom Build) | MIT *
 * https://modernizr.com/download/?-setclasses-testallprops-teststyles !*/
!function (e, n, t) {
    function r(e, n) {
        return typeof e === n
    }

    function o() {
        var e, n, t, o, s, i, l;
        for (var a in S) if (S.hasOwnProperty(a)) {
            if (e = [], n = S[a], n.name && (e.push(n.name.toLowerCase()), n.options && n.options.aliases && n.options.aliases.length)) for (t = 0; t < n.options.aliases.length; t++) e.push(n.options.aliases[t].toLowerCase());
            for (o = r(n.fn, "function") ? n.fn() : n.fn, s = 0; s < e.length; s++) i = e[s], l = i.split("."), 1 === l.length ? Modernizr[l[0]] = o : (!Modernizr[l[0]] || Modernizr[l[0]] instanceof Boolean || (Modernizr[l[0]] = new Boolean(Modernizr[l[0]])), Modernizr[l[0]][l[1]] = o), C.push((o ? "" : "no-") + l.join("-"))
        }
    }

    function s(e) {
        var n = _.className, t = Modernizr._config.classPrefix || "";
        if (x && (n = n.baseVal), Modernizr._config.enableJSClass) {
            var r = new RegExp("(^|\\s)" + t + "no-js(\\s|$)");
            n = n.replace(r, "$1" + t + "js$2")
        }
        Modernizr._config.enableClasses && (n += " " + t + e.join(" " + t), x ? _.className.baseVal = n : _.className = n)
    }

    function i() {
        return "function" != typeof n.createElement ? n.createElement(arguments[0]) : x ? n.createElementNS.call(n, "http://www.w3.org/2000/svg", arguments[0]) : n.createElement.apply(n, arguments)
    }

    function l() {
        var e = n.body;
        return e || (e = i(x ? "svg" : "body"), e.fake = !0), e
    }

    function a(e, t, r, o) {
        var s, a, u, f, c = "modernizr", p = i("div"), d = l();
        if (parseInt(r, 10)) for (; r--;) u = i("div"), u.id = o ? o[r] : c + (r + 1), p.appendChild(u);
        return s = i("style"), s.type = "text/css", s.id = "s" + c, (d.fake ? d : p).appendChild(s), d.appendChild(p), s.styleSheet ? s.styleSheet.cssText = e : s.appendChild(n.createTextNode(e)), p.id = c, d.fake && (d.style.background = "", d.style.overflow = "hidden", f = _.style.overflow, _.style.overflow = "hidden", _.appendChild(d)), a = t(p, e), d.fake ? (d.parentNode.removeChild(d), _.style.overflow = f, _.offsetHeight) : p.parentNode.removeChild(p), !!a
    }

    function u(e, n) {
        return !!~("" + e).indexOf(n)
    }

    function f(e) {
        return e.replace(/([a-z])-([a-z])/g, function (e, n, t) {
            return n + t.toUpperCase()
        }).replace(/^-/, "")
    }

    function c(e, n) {
        return function () {
            return e.apply(n, arguments)
        }
    }

    function p(e, n, t) {
        var o;
        for (var s in e) if (e[s] in n) return t === !1 ? e[s] : (o = n[e[s]], r(o, "function") ? c(o, t || n) : o);
        return !1
    }

    function d(e) {
        return e.replace(/([A-Z])/g, function (e, n) {
            return "-" + n.toLowerCase()
        }).replace(/^ms-/, "-ms-")
    }

    function m(n, t, r) {
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

    function y(n, r) {
        var o = n.length;
        if ("CSS" in e && "supports" in e.CSS) {
            for (; o--;) if (e.CSS.supports(d(n[o]), r)) return !0;
            return !1
        }
        if ("CSSSupportsRule" in e) {
            for (var s = []; o--;) s.push("(" + d(n[o]) + ":" + r + ")");
            return s = s.join(" or "), a("@supports (" + s + ") { #modernizr { position: absolute; } }", function (e) {
                return "absolute" == m(e, null, "position")
            })
        }
        return t
    }

    function v(e, n, o, s) {
        function l() {
            c && (delete N.style, delete N.modElem)
        }

        if (s = r(s, "undefined") ? !1 : s, !r(o, "undefined")) {
            var a = y(e, o);
            if (!r(a, "undefined")) return a
        }
        for (var c, p, d, m, v, g = ["modernizr", "tspan", "samp"]; !N.style && g.length;) c = !0, N.modElem = i(g.shift()), N.style = N.modElem.style;
        for (d = e.length, p = 0; d > p; p++) if (m = e[p], v = N.style[m], u(m, "-") && (m = f(m)), N.style[m] !== t) {
            if (s || r(o, "undefined")) return l(), "pfx" == n ? m : !0;
            try {
                N.style[m] = o
            } catch (h) {
            }
            if (N.style[m] != v) return l(), "pfx" == n ? m : !0
        }
        return l(), !1
    }

    function g(e, n, t, o, s) {
        var i = e.charAt(0).toUpperCase() + e.slice(1), l = (e + " " + P.join(i + " ") + i).split(" ");
        return r(n, "string") || r(n, "undefined") ? v(l, n, o, s) : (l = (e + " " + z.join(i + " ") + i).split(" "), p(l, n, t))
    }

    function h(e, n, r) {
        return g(e, t, t, n, r)
    }

    var C = [], S = [], w = {
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
            S.push({name: e, fn: n, options: t})
        },
        addAsyncTest: function (e) {
            S.push({name: null, fn: e})
        }
    }, Modernizr = function () {
    };
    Modernizr.prototype = w, Modernizr = new Modernizr;
    var _ = n.documentElement, x = "svg" === _.nodeName.toLowerCase(), b = (w.testStyles = a, "Moz O ms Webkit"),
        P = w._config.usePrefixes ? b.split(" ") : [];
    w._cssomPrefixes = P;
    var z = w._config.usePrefixes ? b.toLowerCase().split(" ") : [];
    w._domPrefixes = z;
    var E = {elem: i("modernizr")};
    Modernizr._q.push(function () {
        delete E.elem
    });
    var N = {style: E.elem.style};
    Modernizr._q.unshift(function () {
        delete N.style
    }), w.testAllProps = g, w.testAllProps = h, o(), s(C), delete w.addTest, delete w.addAsyncTest;
    for (var j = 0; j < Modernizr._q.length; j++) Modernizr._q[j]();
    e.Modernizr = Modernizr
}(window, document);
Modernizr.on('webp', function (result) {
    if (result) {
        console.log("yes there is webp here")
    } else {
        // not-supported
        console.log("no there is no webp here, consider png")
    }
    var x = document.querySelector("html");
    console.log("after test: " + x)
});