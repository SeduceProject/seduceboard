window.onload=function(){

    $.getJSON("/weighted_tree_consumption_data", function(cons_obj) {
        var json = cons_obj;

        /*var width = 700;
        var height = 450;
        var maxLabel = 150;
        var duration = 500;
        var radius = 1;

        var i = 0;
        var root;*/
//
//        var realWidth = 700;
//        var realHeight = 450;

        var realWidth = window.innerWidth;
        var realHeight = window.innerHeight;

        var maxLabel = 150;
        var duration = 500;
        var radius = 1;

        var m = [0, 240, 0, 100],
            width = realWidth -m[0] -m[0],
            height = realHeight -m[0] -m[2],
            i = 0,
            root;


        var tree = d3.layout.tree()
          .size([height, width]);



        var diagonal = d3.svg.diagonal()
          .projection(function(d) {
            return [d.y, d.x];
          });



        var botao = d3.select("#form #button");

        /*var svg = d3.select("body").append("svg")
          .attr("width", width)
          .attr("height", height)
          .append("g")
          .attr("transform", "translate(" + maxLabel + ",0)");*/

        var svg = d3.select("#tree").append("svg")
          .attr("id", "tree_svg")
          .attr("width", width)
          .attr("height", height)
            .style("overflow", "scroll")
            .style("background-color","#EEEEEE")
          .append("svg:g")
            .attr("class","drawarea")
          .append("svg:g")
            .attr("transform", "translate(" + m[3] + "," + m[0] + ")");


        function resize() {
            var width = window.innerWidth, height = window.innerHeight;
            $("#tree_svg").width(width).height(height);
        }
        window.addEventListener('resize', resize);

        root = json;
        root.x0 = height / 2;
        root.y0 = 0;

        //root.children.forEach(collapse);

        function update(source) {
          // Compute the new tree layout.
          var nodes = tree.nodes(root).reverse();
          var links = tree.links(nodes);

          // Normalize for fixed-depth.
          nodes.forEach(function(d) {
            d.y = d.depth * maxLabel;
          });

          // Update the nodes…
          var node = svg.selectAll("g.node")
            .data(nodes, function(d) {
              return d.id || (d.id = ++i);
            });

          // Enter any new nodes at the parent's previous position.
          var nodeEnter = node.enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", function(d) {
              return "translate(" + source.y0 + "," + source.x0 + ")";
            })
//            .on("click", click);

          nodeEnter.append("circle")
            .attr("r", 0)
            .style("fill", function(d) {
              return d._children ? "lightsteelblue" : "white";
            });

          nodeEnter.append("text")
            .attr("x", function(d) {
              var spacing = computeRadius(d) + 5;
              return d.children || d._children ? -spacing : spacing;
            })
            .attr("dy", "3")
            .attr("text-anchor", function(d) {
              return d.children || d._children ? "end" : "start";
            })
            .text(function(d) {
              return d.name;
            })
            .on("mouseover", function(d){
                d3.select(this).attr('transform', function(d){ return 'translate(?,?)'})
                .attr("font-size", "20px");
              })
              .on("mouseout", function(d){
                      d3.select(this).attr('transform', function(d){ return 'translate(?,?)'})
                .attr("font-size", "10px");
                })
            .style("fill-opacity", 0);

          // Transition nodes to their new position.
          var nodeUpdate = node.transition()
            .duration(duration)
            .attr("transform", function(d) {
              return "translate(" + d.y + "," + d.x + ")";
            });

          nodeUpdate.select("circle")
            .attr("r", function(d) {
              return computeRadius(d);
            })
            .style("fill", function(d) {
              return d._children ? "lightsteelblue" : "#fff";
            });

          nodeUpdate.select("text").style("fill-opacity", 1);

          // Transition exiting nodes to the parent's new position.
          var nodeExit = node.exit().transition()
            .duration(duration)
            .attr("transform", function(d) {
              return "translate(" + source.y + "," + source.x + ")";
            })
            .remove();

          nodeExit.select("circle").attr("r", 0);
          nodeExit.select("text").style("fill-opacity", 0);

          // Update the links…
          var link = svg.selectAll("path.link")
            .data(links, function(d) {
              return d.target.id;
            });

          // Enter any new links at the parent's previous position.
          link.enter().insert("path", "g")
            .attr("class", "link")
            .style("stroke", "lightgray" )
         /*   .on("mouseover", function(d){
                d3.select(this).attr('transform', function(d){ return 'translate(?,?)'})
                .style("stroke", "black" )
                d3.select(source.name).attr('transform', function(d){ return 'translate(?,?)'})
                        .text("toto")
              })
             .on("mouseout",function(d){
                d3.select(this).attr('transform', function(d){ return 'translate(?,?)'})
                .style("stroke", "lightgray" )
              })*/
            .style("stroke-width", function(d) {
              var widthLink = 0;
              return 50 * ((d.target.h+0.1) / 100);
            })
            .attr("d", function(d) {
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
            .attr("d", diagonal);

          // Transition exiting nodes to the parent's new position.
          link.exit().transition()
            .duration(duration)
            .attr("d", function(d) {
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
          nodes.forEach(function(d) {
            d.x0 = d.x;
            d.y0 = d.y;
          });
        }

        function computeRadiusb(d) {
          if (d.children || d._children) return radius + (radius * nbEndNodes(d) / 2 );
          else return radius;
        }

        function computeRadius(d) {
        //50 * ((d.target.h+0.1) / 100)
          if (d.children || d._children) return (25 * ((d.h) / 100 ));
          else return (25 * ((d.h+0.1) / 100 ));
        }

        function comuteRR(d){
        return d.h;
        }

        function nbEndNodes(n) {
          nb = 0;
          if (n.children) {
            n.children.forEach(function(c) {
              nb += nbEndNodes(c);
            });
          } else if (n._children) {
            n._children.forEach(function(c) {
              nb += nbEndNodes(c);
            });
          } else nb++;

          return nb;
        }

//        function click(d) {
//          if (d.children) {
//            d._children = d.children;
//            d.children = null;
//          } else {
//            d.children = d._children;
//            d._children = null;
//          }
//          update(d);
//        }

//        function collapse(d) {
//          if (d.children) {
//            d._children = d.children;
//            d._children.forEach(collapse);
//            d.children = null;
//          }
//        }


        setInterval(function(){

            console.log("reloading");
            $.getJSON("/weighted_tree_consumption_data", function(cons_obj) {
                update(cons_obj);
            });

        }, 5000);
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