/* eslint-env browser */
/* global $, d3*/

/* eslint-disable no-console */

function load_weighted_tree_consumption(select_function, unselect_function) {
    window.onload = function () {

        $.getJSON("/weighted_tree_consumption_data", function (cons_obj) {
            var json = cons_obj;

            var realWidth = window.innerWidth;
            var realHeight = window.innerHeight;

            var maxLabel = 200;
            var duration = 500;
            var radius = 1;

            var m = [0, 240, 0, 100],
                width = realWidth - m[0] - m[0],
                height = realHeight - m[0] - m[2],
                i = 0,
                root;

            var tree = d3.layout.tree()
                .size([height, width]);
            window.tree = tree;

            var diagonal = d3.svg.diagonal()
                .projection(function (d) {
                    return [d.y, d.x];
                });

            var svg = d3.select("#tree").append("svg")
                .attr("id", "tree_svg")
                .attr("width", width)
                .attr("height", height)
                .style("overflow", "scroll")
                .style("background-color", "#EEEEEE")
                .append("svg:g")
                .attr("class", "drawarea")
                .append("svg:g")
                .attr("transform", "translate(" + m[3] + "," + m[0] + ")");


            function resize() {
                var width = window.innerWidth, height = window.innerHeight;
                $("#tree_svg").width(width).height(height);
            }

            window.addEventListener("resize", resize);

            root = json;
            root.x0 = height / 2;
            root.y0 = 0;

            window.root = root;

            function update(source) {

                // Compute the new tree layout.
                var nodes = tree.nodes(source).reverse();
                var links = tree.links(nodes);

                // Normalize for fixed-depth.
                nodes.forEach(function (d) {
                    d.y = d.depth * maxLabel;
                });

                // Update the nodes…
                var node = svg.selectAll("g.node")
                    .data(nodes, function (d) {
                        return d.id || (d.id = ++i);
                    });

                // Enter any new nodes at the parent's previous position.
                var nodeEnter = node.enter()
                    .append("g")
                    .attr("class", "node")
                    .attr("transform", function (d) {
                        return "translate(" + source.y0 + "," + source.x0 + ")";
                    })

                nodeEnter.append("circle")
                    .attr("r", 0)
                    .attr("id", function (d) {
                        return d.id + "_circle";
                    })
                    .style("fill", function (d) {
                        return d._children ? "lightsteelblue" : "white";
                    });

                nodeEnter.append("text")
                    .attr("x", function (d) {
                        var spacing = computeRadius(d) + 5;
                        return d.children || d._children ? -spacing : spacing;
                    })
                    .style("font-size", function(d) {
                        let map_level_fontsize = {
                            0: "34px",
                            1: "27px",
                            2: "20px",
                            3: "12px",
                            4: "10px",
                            5: "5px",
                            6: "5px",
                        }
                        return map_level_fontsize[d.level];
                    })
                    .attr("dy", "3")
                    .attr("class", "unselected_tree_element")
                    .attr("text-anchor", function (d) {
                        return d.children || d._children ? "end" : "start";
                    })
                    .text(function (d) {
                        return d.name;
                    })
                    .on("click", function (data) {
                        let element = d3.select(this);
                        if (data["click_count"] == undefined) {
                            data["click_count"] = 0;
                        } else {
                            data["click_count"] += 1;
                        }
                        if (data["click_count"] % 2 == 0) {
                            select_function(element, data);
                        } else {
                            unselect_function(element, data);
                        }
                    })
                    .style("fill-opacity", 0);

                // Transition nodes to their new position.
                var nodeUpdate = node.transition()
                    .duration(duration)
                    .attr("transform", function (d) {
                        if (d.h > 20) {
                            d.x -= d.h;
                        }
                        console.log("translate(" + d.y + "," + d.x + ", "+ d.h +")");
                        return "translate(" + d.y + "," + d.x + ")";
                    });

                nodeUpdate.select("circle")
                    .attr("r", function (d) {
                        return computeRadius(d);
                    })
                    .style("fill", function (d) {
                        return d._children ? "lightsteelblue" : "#fff";
                    });

                nodeUpdate.select("text").style("fill-opacity", 1);

                // Transition exiting nodes to the parent's new position.
                var nodeExit = node.exit().transition()
                    .duration(duration)
                    .attr("transform", function (d) {
                        return "translate(" + source.y + "," + source.x + ")";
                    })
                    .remove();

                nodeExit.select("circle").attr("r", 0);
                nodeExit.select("text").style("fill-opacity", 0);

                // Update the links…
                var link = svg.selectAll("path.link")
                    .data(links, function (d) {
                        return d.target.id;
                    });

                // Enter any new links at the parent's previous position.
                link.enter().insert("path", "g")
                    .attr("class", "link")
                    .style("stroke", "lightgray")
                    .style("stroke-width", function (d) {
                        return 50 * ((d.target.h + 0.1) / 100);
                    })
                    .attr("d", function (d) {
                        var o = {
                            x: source.x0,
                            y: source.y0
                        };
                        return diagonal({
                            source: o,
                            target: o
                        });
                    });

                // Transition links to their new position.
                link.transition()
                    .duration(duration)
                    .style("stroke-width", function (d) {
                        return 50 * ((d.target.h + 0.1) / 100);
                    })
                    .attr("d", diagonal);

                // Transition exiting nodes to the parent's new position.
                link.exit().transition()
                    .duration(duration)
                    .attr("d", function (d) {
                        var o = {
                            x: source.x,
                            y: source.y
                        };
                        return diagonal({
                            source: o,
                            target: o
                        });
                    })
                    .remove();

                // Stash the old positions for transition.
                nodes.forEach(function (d) {
                    d.x0 = d.x;
                    d.y0 = d.y;
                });
            }

            function update_radius(source) {
                console.log(source+ ", "+ window.tree);
                update(source);
            }

            function computeRadius(d) {
                if ((d.children || d._children)) return (25 * ((d.h) / 100 ));
                else return (25 * ((d.h + 0.1) / 100 ));
            }

            setInterval(function () {

                console.log("reloading");
                $.getJSON("/weighted_tree_consumption_data", function (cons_obj) {
                    update_radius(cons_obj);
                });

            }, 5 * 1000);

            update(root);

            d3.select("svg")
                .call(d3.behavior.zoom()
                    .scaleExtent([0.5, 5])
                    .on("zoom", zoom));

            function zoom() {
                var scale = d3.event.scale,
                    translation = d3.event.translate,
                    tbound = -height * scale,
                    bbound = height * scale,
                    lbound = (-width + m[1]) * scale,
                    rbound = (width - m[3]) * scale;
                // limit translation to thresholds
                translation = [
                    Math.max(Math.min(translation[0], rbound), lbound),
                    Math.max(Math.min(translation[1], bbound), tbound)
                ];
                d3.select(".drawarea")
                    .attr("transform", "translate(" + translation + ")" +
                        " scale(" + scale + ")");
            }
        });
    }
}