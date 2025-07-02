const BTeditor = ace.edit("behaviour-tree-display");
BTeditor.setTheme("ace/theme/monokai");
BTeditor.session.setMode("ace/mode/json");
BTeditor.setOption("copyWithEmptySelection", true);
BTeditor.setOptions({
    fontSize: "12px",
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
    showPrintMargin: false
});

const { BehaviourTree, State } = mistreevous;

const behaviourTreeEditor = document.getElementById("behaviour-tree-display");
var treeDefinition, agent, tree;
var ballVisible = false;
var ballFront = false;

var blackboard = {
    "thisPos": [0, -50],
    "ballPos": [0, 0],
    "turnDirection": null,
    "targetPos": null
};

agent = {
    driveToGoal: () => {console.log("driveToGoal"); return State.SUCCEEDED;},
    driveToBall: () => {console.log("driveToBall"); return State.SUCCEEDED;},
    predictBallPath: () => {console.log("predictBallPath"); return State.SUCCEEDED;},
    collectBall: () => {console.log("collectBall"); return State.SUCCEEDED;},
    determineSide: () => {console.log("determineSide"); return State.SUCCEEDED;},
    saveTurnDirectionToBlackboard: () => {blackboard["turnDirection"] = 0; console.log("saveTurnDirectionToBlackboard"); return State.SUCCEEDED;},
    saveTargetPosToBlackboard: () => {blackboard["targetPos"] = [50, 50]; console.log("saveTargetPosToBlackboard"); return State.SUCCEEDED;},
    turnToFaceDirection: () => {console.log("turnToFaceDirection"); return State.SUCCEEDED;},
    driveToTargetPos: () => {console.log("driveToTargetPos"); return State.SUCCEEDED;},
    turnToFaceGoal: () => {console.log("turnToFaceGoal"); return State.SUCCEEDED;},
    shoot: () => {console.log("shoot"); return State.SUCCEEDED;},

    checkIfBallIsNotVisible: () => {if (!ballVisible) {return State.SUCCEEDED;} else {return State.FAILED;}},
    checkIfBallIsVisible: () => {if (ballVisible) {return State.SUCCEEDED;} else {return State.FAILED;}},
    conditionBallBehind: () => {if (!ballFront) {return State.SUCCEEDED;} else {return State.FAILED;}},
    conditionBallFront: () => {if (ballFront) {return State.SUCCEEDED;} else {return State.FAILED;}}
};

function startTree() {
    tree = new BehaviourTree(treeDefinition, agent);
    tree.step();
}

function loadTree() {
    fetchTree().then(data => {
        treeDefinition = JSON.parse(data);
        BTeditor.session.setValue(JSON.stringify(treeDefinition, null, 4));
        console.log(treeDefinition);
        
        startTree();
    });
}

function fetchTree() {
    return fetch(`/bt`, {
        method: 'POST',
        body: ""
    }).then(response => response.text())
}
function saveTree(_json) {
    return fetch(`/bt`, {
        method: 'POST',
        body: JSON.stringify(_json)
    }).then(response => response.text())
}

window.addEventListener("load", () => {setTimeout("loadTree();", 1000)});
behaviourTreeEditor.addEventListener("input", () => {
    try {
        treeDefinition = JSON.parse(behaviourTreeEditor.value);
        saveTree(treeDefinition);
    } catch (e) {
        console.log("Invalid ", e);
    }
});