function doesRectangleOverlap(a, b) {
	  return (Math.abs(a.x - b.x) * 2 < (a.width + b.width)) &&
	         (Math.abs(a.y - b.y) * 2 < (a.height + b.height));
}

// used for collision detection, and keep out behavior of nodes
function nodeColisionResolver(node) {
	  var nx1, nx2, ny1, ny2, padding;
	  padding = 32;
	  function x2(node){
		  return node.x + node.width; 
	  }
	  function y2(node){
		  return node.y + node.height; 
	  }
	  nx1 = node.x - padding;
	  nx2 = x2(node) + padding;
	  ny1 = node.y - padding;
	  ny2 = y2(node.y) + padding;
	  
	  
	  return function(quad, x1, y1, x2, y2) {
	    var dx, dy;
		function x2(node){
		 return node.x + node.width; 
		}
		function y2(node){
		 return node.y + node.height; 
		}
	    if (quad.point && (quad.point !== node)) {
	      if (doesRectangleOverlap(node, quad.point)) {
	        dx = Math.min(x2(node)- quad.point.x, x2(quad.point) - node.x) / 2;
	        node.x -= dx;
	        quad.point.x -= dx;
	        dy = Math.min(y2(node) - quad.point.y,y2(quad.point) - node.y) / 2;
	        node.y -= dy;
	        quad.point.y += dy;
	      }
	    }
	    return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
	  };
};

function netMouseOver() {
	var net = d3.select(this)[0][0].__data__.net;
	d3.selectAll(".link")
	  .classed("link-selected", 
			  function(d){
		  			return d.net === net
	  		  });
}
function netMouseOut() {
	d3.selectAll(".link")
	  .classed("link-selected", false);
}

function addShadows(svg){
	// filters go in defs element
	var defs = svg.append("defs");

	// create filter with id #drop-shadow
	// height=130% so that the shadow is not clipped
	var filter = defs.append("filter")
	    .attr("id", "drop-shadow")
	    .attr("height", "130%");

	// SourceAlpha refers to opacity of graphic that this filter will be applied to
	// convolve that with a Gaussian with standard deviation 3 and store result
	// in blur
	filter.append("feGaussianBlur")
	    .attr("in", "SourceAlpha")
	    .attr("stdDeviation", 1)
	    .attr("result", "blur");

	// translate output of Gaussian blur to the right and downwards with 2px
	// store result in offsetBlur
	filter.append("feOffset")
	    .attr("in", "blur")
	    .attr("dx", 2)
	    .attr("dy", 2)
	    .attr("result", "offsetBlur");

	// overlay original SourceGraphic over translated blurred opacity by using
	// feMerge filter. Order of specifying inputs is important!
	var feMerge = filter.append("feMerge");

	feMerge.append("feMergeNode")
	    .attr("in", "offsetBlur")
	feMerge.append("feMergeNode")
	    .attr("in", "SourceGraphic");

	//gradient
	var minY = 10;
	var maxY = 210;

	var gradient = svg
		.append("linearGradient")
		.attr("y1", minY)
		.attr("y2", maxY)
		.attr("x1", "0")
		.attr("x2", "0")
		.attr("id", "gradient")
		.attr("gradientUnits", "userSpaceOnUse")
    
	gradient
	.append("stop")
	.attr("offset", "0")
	.attr("stop-color", "#E6E6E6")
    
	gradient
    .append("stop")
    .attr("offset", "0.5")
    .attr("stop-color", "#A9D0F5")    
}

function updateNetLayout(svgGroup, linkElements, nodes, links){ // move component on its positions and redraw links between them
	//move component on its position

	var router = new NetRouter(nodes, links);
	var grid = router.grid;
	router.route();
	
	//create debug dots for routing nodes
	(function debugRouterDots(){
		var toolTipDiv = d3.select("body")
			.append("div")   
		    .attr("id", "tooltip")               
		    .style("opacity", 0);
		var flatenMap = [];
		grid.visitFromLeftTop(function(c){
			flatenMap.push(c);
		});
		svgGroup.selectAll("circle")
			.data(flatenMap)
			.enter().append("circle")
			.style("fill", "steelblue")
			.attr("r", 2)
			.attr("cx", function(d){
				return d.pos()[0];
			})
			.attr("cy", function(d){
				return d.pos()[1];
			}) 
		    .on("mouseover", function(d) {
		    	var html = d.pos() + "</br><b>horizontal:</b><ol>"
					d.horizontal.forEach(function (net){
						if (net)
							html += "<li>" + net.name  + "</li>";
					});
		    	html += "</ol><b>vertical:</b><ol>";
		    	d.vertical.forEach(function (net){
		    		if (net)
		    			html += "<li>" + net.name  + "</li>";
				});
		    	html += "</ol>";
		    	
		    	
		    	toolTipDiv.transition()        
		            .duration(100)      
		            .style("opacity", .9);      
		    	toolTipDiv.html(html)
		            .style("left", d3.event.pageX + "px")     
		            .style("top", (d3.event.pageY - 28) + "px");    
		    })                  
		    .on("mouseout", function(d) {       
		    	toolTipDiv.transition()        
		            .duration(200)      
		            .style("opacity", 0);   
		    });
		
		//// line to parent componet
		//svgGroup.selectAll("#debuglink")
		//	.data(flatenMap)
		//	.enter()
		//	.append("path") 
		//	.classed({"link": true})
		//	.attr("d", function (d) {
		//        var sx = d.pos()[0];
		//        var sy = d.pos()[1];
		//        var tx = d.originComponent.x;
		//        var ty = d.originComponent.y ;
		//        return "M" + sx + "," + sy + " L " + tx + "," + ty;
		//    });
	})();
	

	(function drawNets(){
		function offsetInRoutingNode(node, net){
			var x= 0,
				y= 0;
			
			var xindx= node.vertical.indexOf(net);
			if(xindx > 0)
				x += xindx*NET_PADDING;
			
			var yindx= node.horizontal.indexOf(net);
			if(yindx > 0)
				y += yindx*NET_PADDING;
			
			return [x, y];
		}
		
		
		function pointAdd(a, b){
			a[0] += b[0];
			a[1] += b[1];			
		}
		//print link between them
		linkElements.attr("d", function (d) {
			var sp = d.start.pos();
			var spOffset = offsetInRoutingNode(d.start, d.net);
			var pathStr = " M" + [sp[0] - COMPONENT_PADDING , sp[1]]; //connection from port node to port
			pointAdd(sp, spOffset);
			pathStr += " L " + sp +"\n";
	
			for(var pi = 0; pi< d.path.length; pi++){
				var p = d.path[pi];
				spOffset = offsetInRoutingNode(p, d.net);
				sp = p.pos();
				pointAdd(sp, spOffset);
				pathStr += " L " + sp +"\n";
			}
			var ep = d.end.pos();
			pathStr += " L " + [ep[0]+COMPONENT_PADDING +d.end.originComponent.netChannelPadding.left, ep[1]]+"\n";
			return pathStr;
		});
	})();
};

function redraw(nodes, links){ //main function for rendering components layout
	var wrapper = d3.select("#chartWraper");
	
	wrapper.selectAll("svg").remove(); // delete old on redraw

	var svg = wrapper.append("svg");
	var svgGroup= svg.append("g"); // because of zooming/moving

	addShadows(svg);

	//grid higlight
    var linkElements = svgGroup.selectAll(".link")
    	.data(links)
    	.enter()
    	.append("path")
    	.classed({"link": true})
    	.on("mouseover", netMouseOver)
    	.on("mouseout", netMouseOut);

    updateNetLayout(svgGroup, linkElements, nodes, links);


    var place = svg.node().getBoundingClientRect();
	//force for self organizing of diagram
	var force = d3.layout.force()
		.gravity(.00)
		.distance(150)
		.charge(-2000)
		.size([place.width, place.height])
		//.nodes(nodes)
		//.links(links)
		//.start();
	drawExternalPorts(svgGroup, nodes.filter(function (n){
			return n.isExternalPort;
		}));
	drawComponents(svgGroup, nodes.filter(function (n){
			return !n.isExternalPort;
		}))
		.call(force.drag); //component dragging

    // define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
    var zoomListener = d3.behavior.zoom()
    	.scaleExtent([0.2, 30])
    	.on("zoom", function () {
    			svgGroup.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    	});
    function diagramSize(){
    	var widthMax =0;
    	var heigthtMax = 0;
    	nodes.forEach(function (n){
    		widthMax = Math.max(n.x +n.width + COMPONENT_PADDING, widthMax);
    		heigthtMax = Math.max(n.y + n.height +COMPONENT_PADDING, heigthtMax);
    	});
    	return [widthMax, heigthtMax];
    }
    var size = diagramSize();
    var scaleX = place.width /size[0] ;
    var scaleY = place.height / size[1];
    var scale = Math.min(scaleX, scaleY); 
    
    //this is processiong of zoomListener explicit translate and scale on start
    zoomListener.translate([0,0])
    	.scale(scale);
    zoomListener.event(svg.transition()
    					  .duration(100));
    
    svg.call(zoomListener);
 
}