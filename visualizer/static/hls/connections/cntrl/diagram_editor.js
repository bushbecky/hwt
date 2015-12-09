function diagramEditorCntrl($scope, hotkeys){
	var api = $scope.$parent.api;
	var addDialog = $("#newComponent");
	api.editedObject = {}
	$scope.newObject = {
		"name" : "",
		"id": "",
		"type" : "",
		"inputs" : [],
		"outputs" : []
	}
	$scope.portarrays = [];

	
	hotkeys.template = '<div class="cfp-hotkeys-container fade" ng-class="{in: helpVisible}" style="display: none;"><div class="cfp-hotkeys">' +
    '<h4 class="cfp-hotkeys-title" ng-if="!header">{$ title $}</h4>' +
    '<div ng-bind-html="header" ng-if="header"></div>' +
    '<table><tbody>' +
      '<tr ng-repeat="hotkey in hotkeys | filter:{ description: \'!$$undefined$$\' }">' +
        '<td class="cfp-hotkeys-keys">' +
          '<span ng-repeat="key in hotkey.format() track by $index" class="cfp-hotkeys-key">{$ key $}</span>' +
        '</td>' +
        '<td class="cfp-hotkeys-text">{$ hotkey.description $}</td>' +
      '</tr>' +
    '</tbody></table>' +
    '<div ng-bind-html="footer" ng-if="footer"></div>' +
    '<div class="cfp-hotkeys-close" ng-click="toggleCheatSheet()">×</div>' +
    '</div></div>';
    
	hkBindings = [
			{
				combo: 'ctrl+a',
				description: 'Add component',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					//console.log("A hotkey");
					api.componentAdd();
				}
			},
			{
				combo: 'ctrl+s',
				description: 'Save file',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					//console.log("S hotkey");
					api.save(api.openedFile);
				}
			},
			{
				combo: 'ctrl+shift+s',
				description: 'Sav file as',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					//console.log("Shift S hotkey");
					api.fileDialog(true);
				}
			},
			{
				combo: 'ctrl+d',
				description: 'Delete component',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					//console.log("D hotkey");
					api.objectDelete();
				}
			},
			{
				combo: 'ctrl+q',
				description: 'Redraw state',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					//console.log("Q hotkey");
					api.redraw();
				}
			},
			{
				combo: 'ctrl+e',
				description: 'Edit component',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					console.log("E hotkey");
				}
			},
			{
				combo: 'ctrl+o',
				description: 'Open new file',
				callback: function(e) {
					e.stopPropagation(this);
					e.preventDefault(this);
					//console.log("O hotkey");
					api.fileDialog(false);
				}
			}
	]
	
	for (var key in hkBindings)
	{
		//console.log(hkBindings[key]);
		hotkeys.add({
		    combo: hkBindings[key].combo,
		    description: hkBindings[key].description,
		    callback: hkBindings[key].callback
		  });
	}

	
	
	$scope.dismissAddDialog = function() {
		addDialog.modal('hide');
	}
		
	api.insertNode = function(node, x, y){
		api.nodes.push(node);
		//[TODO] x,y
	}
	
	api.synthetize = function(){
		function onHidden(){
			console.log('goodbye'); 
		}
		var f = api.openedFile;
		
		var msg = api.msg.info("Synhetizing", f, {timeOut: 0})
		setTimeout(function(){
			api.msg.clear(msg);
			api.msg.success("Synthetized ",f, {});
		}, 10000);

	}
	
	api.componentEditDetail = function() {
		// console.log("Component Detail")
		var selection = d3.selectAll(".selected-object");
		var count = selection[0].length
		if (count == 0) {
			api.msg.error("No object selected!")
		} else if (count > 1) {
			api.msg.error("Too many objects selected!")
		} else {
			d3.selectAll("#componentEdit").style("display", "block");

			// console.log(selection[0][0])
			var object = selection[0][0]
			var selected = object.getElementsByTagName("g");
			// console.log(object.__data__)
			$scope.editedObject = object.__data__;
			$scope.portarrays = [ {
				'array' : $scope.editedObject.inputs,
				'name' : 'Inputs'
			}, {
				'array' : $scope.editedObject.outputs,
				'name' : 'Outputs'
			} ]
		}

	}

	$scope.componentRemovePort = function(object, group, port) {
		console.log("ComponentEditRemovePort")
		// console.log(object, group, port);
		var portGroup = (group == 'Inputs' ? object.inputs : object.outputs)
		// console.log(portGroup, port);
		var index = portGroup.indexOf(port);
		if (index > -1) {
			portGroup.splice(index, 1);
		} else {
			console.log("Remove port error: port does not exist")
		}
		// componentEdit redraw
		// api.redraw();
	}


	$scope.componentAddPort = function(object, group) {
		var portGroup = (group == 'Inputs' ? object.inputs : object.outputs);
		portGroup.push({
			"name" : ""
		});
	}

	$scope.componentEditSubmit = function() {
		api.redraw();
		//console.log("Submit")
		//console.log($scope.editedObject.inputs)
		// d3.selectAll("#componentEdit").style("display", "none");
	}

	$scope.componentEditCancel = function() {
		//console.log("Cancel")
		d3.selectAll("#componentEdit").style("display", "none");
	}

	api.objectDelete = function() {
		// All selected objects
		var objects = d3.selectAll(".selected-object")[0];
		var links = d3.selectAll(".selected-link")[0];
		//console.log("Selected objects", objects);
		//console.log("Selected links", links.length, links);
		for (i = 0; i < objects.length; i++) {
			var obj = objects[i].__data__;
			// console.log(obj)
			// console.log("Nodes: ", api.nodes)
			// console.log("Nets: ", api.nets)
			// console.log("Object check")
			// For all nodes in scope
			for (var i = 0; i < api.nodes.length; i++) {
				// console.log(api.nodes[i].name)
				// Delete matching objects
				if (api.nodes[i].name == obj.name) {
					api.nodes.splice(i, 1);
				}
			}
			//console.log("Nets", obj.id)
			// For all nets in scope
			for (var j = 0; j < api.nets.length; j++) {
				// For all links
				var net = api.nets[j];
				for (var l = 0; l < net.targets.length; l++) {
					// Delete all links from deleted object
					var target = net.targets[l];
					if ((target.id == obj.id) | (net.source.id == obj.id)) {
						// console.log("Net: ", target, net.source)
						var removed = api.nets.splice(j, 1);
						j--;
						break;
					}
				}// for net targets
			}// for scope nets
		}// for selected objects

		//console.log("Link check")
		// For all selected links
		for (var m = 0; m < links.length; m++) {
			var net = links[m].__data__.net;
			var index = api.nets.indexOf(net);
			// Delete all selected links
			if (index > -1) {
				api.nets.splice(index, 1);
			}
		}
		// console.log(api.nets)
		api.redraw();
		return;
	}

	function getComponentID(){
		var max = -1;
		for (var i = 0; i< api.nodes.length; i++)
		{
			if (api.nodes[i].id > max)
			{
				max = api.nodes[i].id;
			}
		}
		//console.log("Maximum: ", max);
		return max;
	}
	

		
	api.componentAdd = function() {
		
		addDialog.modal('show');
		d3.selectAll("#componentAdd").style("display", "block");
		var id = getComponentID();
		$scope.newObject = {
			"name" : "",
			"id": id+1,
			"type" : "",
			"inputs" : [],
			"outputs" : []
		}
		$scope.portarrays = [ {
			'array' : $scope.newObject.inputs,
			'name' : 'Inputs'
		}, {
			'array' : $scope.newObject.outputs,
			'name' : 'Outputs'
		} ]
	}

	$scope.componentAddSubmit = function() {
		console.log("Submit")
		console.log("Before: ", api.nodes)
		$scope.newObject.id = parseInt($scope.newObject.id)
		if($scope.newObject.name == "")
		{
			api.msg.error("Can't create component without name", "Component add error");
			return;
		}
		if(($scope.newObject.inputs.length == 0) && ($scope.newObject.outputs.length == 0))
		{
			api.msg.error("Can't create empty component", "Component add error");
			return;
		}
		
		api.nodes.push($scope.newObject);
		console.log("After: ", api.nodes)
		$("#newComponent").modal('hide')
		
		api.redraw();

		// d3.selectAll("#componentAdd").style("display", "none");
	}

	$scope.componentAddCancel = function() {
		console.log("Cancel")
		d3.selectAll("#componentAdd").style("display", "none");
	}

	$scope.origin = {
		"component" : {},
		"port" : {}
	};
	$scope.destination = {
		"component" : {},
		"port" : {}
	};
	var LINK_STATUS = {
			"none":"none",
			"link" : "link",
			"destination": "destination",
			"origincomp": "origincomp",
			"destinationcomp": "destinationcomp",
	}
	
	$scope.linkstatus = LINK_STATUS.none;
	
	function positionOfElmInDiagram(pos){
		var svg = api.diagramSvg.node()
		var svgPos =  svg.getBoundingClientRect();
		return [pos[0] - svgPos.left,  pos[1] - svgPos.top];
	}
	
	function drawDashedLine2port(elm, mousePossition){
		var line = api.diagramSvg.selectAll('.routing-help-line');
		var portBox=$scope.origin.portElm.children[0].getBoundingClientRect()
		
		if(line.empty()){
			line = api.diagramSvg.append("svg:path")
				       .classed({"routing-help-line": true})
		}
		line
	        .style("stroke-dasharray", ("3, 3"))
	        .attr("d", 'M '+ positionOfElmInDiagram([portBox.right, (portBox.top +portBox.bottom)/2 ]) + "L " + mousePossition );
	}
	
	api.portClick = function(d,elm) {
		switch ($scope.linkstatus) {
		case LINK_STATUS.none:
			$scope.origin.port =d;
			$scope.origin.portElm= elm;
			$scope.linkstatus = LINK_STATUS.origincomp;
			break;
		case LINK_STATUS.destination:
			$scope.destination.port = d;
			$scope.destination.portElm= elm;
			$scope.linkstatus = LINK_STATUS.destinationcomp;
			break;
		}
	}

	api.compClick = function(d) {
		// console.log("Component Click data", d);
		// console.log("Link status", $scope.linkstatus)
		switch ($scope.linkstatus) {
		case LINK_STATUS.origincomp:
			// console.log("Setting origin component")
			$scope.origin.component = d;
			$scope.linkstatus = LINK_STATUS.destination;
			api.onMouseroverDiagram = drawDashedLine2port;
			break;
		case LINK_STATUS.destinationcomp:
			// console.log("Setting destination component")
			$scope.destination.component = d;
			$scope.linkstatus = LINK_STATUS.link;
			break;
		default:
			// console.log("Breaking")
			break;
		}

		// console.log("Link status", $scope.linkstatus)
		// console.log("Origin", $scope.origin)
		// console.log("Destination", $scope.destination)

		if ($scope.linkstatus == LINK_STATUS.link) {
			// console.log("Linking");
			var originportinfo = $scope.getPortIndex($scope.origin.port, $scope.origin.component)
			var destinationportinfo = $scope.getPortIndex($scope.destination.port, $scope.destination.component)
			var net = $scope.makeNet(originportinfo, destinationportinfo,
					$scope.origin.component, $scope.destination.component);

			// console.log("Net to be added: ", net)
			if (net != "") {
				//console.log("Adding net", net)
				api.nets.push(net);
			}
			api.resetLinkingState();
			api.redraw();

		}// if scopestatus link

	}

	$scope.makeNet = function(originport, destinationport, origincomponent,
			destinationcomponent) {
		var origin = {
			"portIndex" : originport[0],
			"id" : origincomponent.id
		}
		var destination = {
			"portIndex" : destinationport[0],
			"id" : destinationcomponent.id
		}
		if (originport[1] == destinationport[1]) {
			api.msg.error("Can't connect matching port groups",
					"QuickLink Erorr")
			return "";
		} else if ((originport[1] == null | destinationport[1] == null)) {
			api.msg.error("Can't connect link port name corrupted",
					"QuickLink Erorr")
			return "";
		}
		// TODO check whether net already exists?
		if (originport[1] == "inputs") {
			net = {
				"targets" : [ origin ],
				"source" : destination
			}
		}// if originport inputs
		else if (originport[1] == "outputs") {
			net = {
				"targets" : [ destination ],
				"source" : origin
			}
		}
		return net;
	}
	
	$scope.getPortIndex= function(port, component){
		var inputIndx = component.inputs.indexOf(port);
		if (inputIndx >= 0)
			return [inputIndx, "inputs"];
		var outputIndx = component.outputs.indexOf(port);
		if (outputIndx >= 0)
			return [outputIndx, "outputs"];
		throw "Can not find port in component";
	}
	
	api.resetLinkingState = function() {
		api.diagramSvg.selectAll('.routing-help-line')
					  .remove();
		api.onMouseroverDiagram = null;
		$scope.linkstatus = LINK_STATUS.none;
	}
}