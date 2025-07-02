const FDcontainer = document.getElementById("fd-dropdown-content");

const FDcanvas = document.getElementById("field-display");
const FDcontext = FDcanvas.getContext("2d");

const ratio = 243 / 182;
let SW = FDcontainer.scrollWidth;
let SH = SW * ratio;
let scale = SW / 182;
if (SH > FDcontainer.scrollHeight) {
    SH = document.documentElement.clientHeight * 0.73;
    SW = SH / ratio;
    scale = SH / 243;
} 
FDcanvas.width = SW;
FDcanvas.height = SH;
FDcanvas.left = FDcontainer.scrollWidth - SW / 2;

function lerp(a, b, t = 0.1) {
    return a + (b - a) * t;
}

function setTargetPos(x, y) {
    fetch(`/target`, {
        method: 'POST',
        body: `${x}, ${y}`
    })
}

class Ball {
    constructor(x, y) {
        this.true_pos = [x, y];
        this.pos = [x, y];
        this.radius = 2.1;
    }
    draw(context) {
        let drawnPos = [(1 + this.pos[0]) * (SW / 2), (1 + this.pos[1]) * (SH / 2) ]
        let radius = this.radius * scale;

        context.beginPath();
        context.arc(drawnPos[0], drawnPos[1], radius, 0, 2 * Math.PI, false);
        context.fillStyle = 'orange';
        context.fill();
        context.lineWidth = 2;
        context.strokeStyle = '#f56642';
        context.stroke();

        context.font = "21px Arial";
        context.fillStyle = "#fff";
        context.fillText(
            `(${Math.round((this.pos[0] + Number.EPSILON) * 1000) / 1000}, ${Math.round((this.pos[1] + Number.EPSILON) * 1000) / 1000})`, 
            drawnPos[0] - 15, drawnPos[1] + 35
        );
    }
}

class Robot {
    constructor(x, y) {
        this.true_pos = [x, y];
        this.pos = [x, y];
        this.radius = 11;
        this.orientation = 0;
        this.viewRadius = 65;
    }
    draw(context) {
        let drawnPos = [(1 + this.pos[0]) * (SW / 2), (1 + this.pos[1]) * (SH / 2) ]
        let radius = this.radius * scale;
        let orientation = -Math.PI / 2 - (Math.PI / 180) * this.orientation

        context.beginPath();
        context.arc(drawnPos[0], drawnPos[1], radius, 0, 2 * Math.PI, false);
        context.fillStyle = 'grey';
        context.fill();
        context.lineWidth = 2;
        context.strokeStyle = '#131313';
        context.stroke();

        context.beginPath();
        context.moveTo(drawnPos[0], drawnPos[1])
        context.lineTo(drawnPos[0] + this.viewRadius * Math.cos(orientation), drawnPos[1] + this.viewRadius * Math.sin(orientation));
        context.lineWidth = 2;
        context.strokeStyle = '#ff0000';
        context.stroke();

        context.font = "21px Arial";
        context.fillStyle = "#fff";
        context.fillText(
            `(${Math.round((this.pos[0] + Number.EPSILON) * 1000) / 1000}, ${Math.round((this.pos[1] + Number.EPSILON) * 1000) / 1000})`, 
            drawnPos[0] - 15, drawnPos[1] + 55
        );
    }
}

const refreshRate = 1.0 / 24;

let ball = new Ball(0, 0);
let mouse = [0, 0];
let rel = [0, 0];
let mouseDown = false;
let canClick = true;
let holding = false;
let db = [0, 0];

let robot = new Robot(0, 0.5);

var fieldOutline = new Path2D();
let dw = 13 * scale;
let dh = 13 * scale;
fieldOutline.moveTo(dw, dh);
fieldOutline.lineTo(dw, SH - dh);
fieldOutline.lineTo(SW - dw, SH - dh);
fieldOutline.lineTo(SW - dw, dh);
fieldOutline.lineTo(dw, dh);
const dotPositions = [
    [52, 57], [182 - 52, 57], [52, 243 - 57], [182 - 52, 243 - 57]
];
function drawField() {
    let m = 13 * scale;
    FDcontext.fillStyle = "#2e7838";
    FDcontext.beginPath();
    FDcontext.moveTo(0, 0);
    FDcontext.lineTo(SW, 0);
    FDcontext.lineTo(SW - m, m);
    FDcontext.lineTo(m, m);
    FDcontext.fill();
    FDcontext.moveTo(0, SH);
    FDcontext.lineTo(SW, SH);
    FDcontext.lineTo(SW - m, SH - m);
    FDcontext.lineTo(m, SH - m);
    FDcontext.fill();

    FDcontext.lineWidth = 2 * scale;

    FDcontext.strokeStyle = "#b7b7b7";
    FDcontext.fillStyle = "#419e4d";
    FDcontext.fill(fieldOutline);
    FDcontext.stroke(fieldOutline);

    FDcontext.strokeStyle = "#0a0a0a";
    FDcontext.fillStyle = "#0a0a0a";
    
    FDcontext.beginPath();
    FDcontext.arc(SW/2, SH/2, 30 * scale, 0, 2 * Math.PI, false)
    FDcontext.stroke()

    for (let i in dotPositions) {
        let pos = dotPositions[i];
        pos = [pos[0] * scale, pos[1] * scale]
        FDcontext.beginPath();
        FDcontext.arc(pos[0], pos[1], 1 * scale, 0, 2 * Math.PI, false)
        FDcontext.fill()
    }

    let x1, x2;
    x1 = (182 - 60) / 2 * scale;
    x2 = (182 + 60) / 2 * scale;
    let y1, y2;
    y1 = 13 * scale;
    y2 = 5 * scale

    // Blue Goal
    FDcontext.beginPath();
    FDcontext.moveTo(x1, 0);
    FDcontext.lineTo(x1, y1);
    FDcontext.stroke()
    FDcontext.moveTo(x2, 0);
    FDcontext.lineTo(x2, y1);
    FDcontext.stroke()
    FDcontext.beginPath();
    FDcontext.strokeStyle = "#0000ff";
    FDcontext.moveTo(x1, y2);
    FDcontext.lineTo(x2, y2);
    FDcontext.stroke()

    // Yellow Goal
    FDcontext.strokeStyle = "#0a0a0a";
    FDcontext.beginPath();
    FDcontext.moveTo(x1, SH);
    FDcontext.lineTo(x1, SH - y1);
    FDcontext.stroke()
    FDcontext.moveTo(x2, SH);
    FDcontext.lineTo(x2, SH - y1);
    FDcontext.stroke()
    FDcontext.beginPath();
    FDcontext.strokeStyle = "#bbbb00";
    FDcontext.moveTo(x1, SH - y2);
    FDcontext.lineTo(x2, SH - y2);
    FDcontext.stroke()

    // Goalie regions
    let r = 15 * scale;
    let y3 = y1 + 10 * scale;
    FDcontext.beginPath();
    FDcontext.moveTo(x1, y1);
    FDcontext.lineTo(x1, y3);
    FDcontext.strokeStyle = "#b7b7b7";
    FDcontext.arc(x1 + r, y3, r, Math.PI, Math.PI / 2, true)
    FDcontext.lineTo(x2 - r, y3 + r);
    FDcontext.arc(x2 - r, y3, r, Math.PI / 2, 0, true)
    FDcontext.lineTo(x2, y1);
    FDcontext.stroke()
    
    FDcontext.beginPath();
    FDcontext.moveTo(x1, SH - y1);
    FDcontext.lineTo(x1, SH - y3);
    FDcontext.strokeStyle = "#b7b7b7";
    FDcontext.arc(x1 + r, SH - y3, r, Math.PI, -Math.PI / 2, false)
    FDcontext.lineTo(x2 - r, SH - (y3 + r));
    FDcontext.arc(x2 - r, SH - y3, r, -Math.PI / 2, 0, false)
    FDcontext.lineTo(x2, SH - y1);
    FDcontext.stroke()
}

const BALL = 0x54;
const ROBOT = 0xef;
let selectedElement = null;

let ticks = 0;
function update() {
    FDcontext.clearRect(0, 0, SW, SH);

    drawField();
    ball.draw(FDcontext);
    robot.draw(FDcontext);

    let squaredDist = Math.pow((ball.pos[0] - mouse[0]) * (SW / 2), 2) + Math.pow((ball.pos[1] - mouse[1]) * (SH / 2), 2);
    if (squaredDist < Math.pow(4 * ball.radius * scale, 2)) {selectedElement = BALL;}
    
    FDcontext.font = "21px Arial";
    FDcontext.fillStyle = "#fff";
    FDcontext.fillText("⇖", (1 + mouse[0]) * SW/2 - 3, (1 + mouse[1]) * SH/2 + 12);

    if (mouseDown || holding) {
        switch (selectedElement) {
            case BALL:
                if (canClick) {
                    let db = [mouse[0] - ball.pos[0], mouse[1] - ball.pos[1]];
                    canClick = false;
                }
                ball.pos[0] = mouse[0] + db[0];
                ball.pos[1] = mouse[1] + db[1];
                holding = true;
                break;
            default:
                break;
        }
    }

    ticks += 1;

    let mouseMoveDistSquared = Math.pow(rel[0], 2) + Math.pow(rel[1], 2)
    if (holding && (ticks % 12 == 0) && mouseMoveDistSquared > 0.0001) {
        setTargetPos(ball.pos[0] * 182, ball.pos[1] * 243)
    }

    setTimeout("update();", refreshRate);
}
update();

FDcanvas.addEventListener("mousemove", (e) => {
    mouseDown = (e.buttons == 1 && e.button == 0);
    if (!mouseDown) {
        canClick = true;
        holding = false;
    }
    if (!holding)
        selectedElement = null;
    rel[0] = -mouse[0];
    rel[1] = -mouse[1];
    mouse[0] = e.offsetX / (SW / 2) - 1; 
    mouse[1] = e.offsetY / (SH / 2) - 1;
    rel[0] += mouse[0];
    rel[1] += mouse[1];
});
FDcanvas.addEventListener("mouseup", (e) => {
    if (e.button != 0 || selectedElement == null)
        return;

    setTargetPos(ball.pos[0] * 182, ball.pos[1] * 243);
})