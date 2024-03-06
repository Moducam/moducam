let width = 1920, height = 1080;
let scale = 1;
// let vertices = [{x: 508, y: 172}, {x: 1434, y: 962}, {x: 1422, y: 482}, {x: 1116, y: 740}, {x: 862, y: 406}, {x: 654, y: 156}, {x: 900, y: 952}, {x: 886, y: 278}];
let vertices = [];
let selectedVertex = null;
let vertexRadius = width / 96;

const sketch = (p) => {
    p.setup = () => {
        let canvas = p.createCanvas(width, height);
        canvas.parent("drawcanvas");
        adjustCanvasScale();
        p.clear();
    };

    p.draw = () => {
        p.clear();

        p.noStroke();
        p.fill(255, 60, 60, 70);
        p.beginShape();
        for (let v of vertices) {
            p.vertex(v.x, v.y);
        }
        p.endShape(p.CLOSE);
        
        for (let v of vertices) {
            p.fill(255, 60, 60);
            p.stroke(0);
            p.strokeWeight(1);
            p.ellipse(v.x, v.y, vertexRadius * (3/4)); // *2
        }
    };

    p.mousePressed = () => {
        // console.log(p.mouseX/scale + " " + p.mouseY/scale + " - " + scale);
        for (let i = 0; i < vertices.length; i++) {
            let d = p.dist(p.mouseX/scale, p.mouseY/scale, vertices[i].x, vertices[i].y);
            if (d < vertexRadius) {
                if (p.mouseButton === p.RIGHT && !selectedVertex) {
                    if (vertices.length > 3)
                        vertices.splice(i, 1);
                } else {
                    selectedVertex = i;
                }
                return;
            }
        }

        if (p.mouseButton !== p.LEFT)
            return;
        // Check for line click to add new point
        for (let i = 0; i < vertices.length; i++) {
            let nextIndex = (i + 1) % vertices.length;
            if (pointLineDistance(p.mouseX/scale, p.mouseY/scale, vertices[i], vertices[nextIndex]) < vertexRadius) {
                vertices.splice(nextIndex, 0, {x: p.mouseX/scale, y: p.mouseY/scale});
                selectedVertex = nextIndex;
                break;
            }
        }
    }

    p.mouseReleased = () => {
        selectedVertex = null;
    }

    p.mouseDragged = () => {
        if (selectedVertex != null) {
            let boundedX = Math.min(Math.max(Math.round(p.mouseX/scale), 0), width)
            let boundedY = Math.min(Math.max(Math.round(p.mouseY/scale), 0), height)
            vertices[selectedVertex].x = boundedX;
            vertices[selectedVertex].y = boundedY;
        }
    }

    function pointLineDistance(px, py, v1, v2) {
        const dx = v2.x - v1.x;
        const dy = v2.y - v1.y;
        const mag = Math.sqrt(dx * dx + dy * dy);
        const u = ((px - v1.x) * dx + (py - v1.y) * dy) / (mag * mag);
    
        if (u > 1 || u < 0) {
            // Closest point does not fall within the line segment, take the shorter distance
            // to an endpoint
            return Math.min(p.dist(px, py, v1.x, v1.y), p.dist(px, py, v2.x, v2.y));
        }
    
        // Compute projected point
        const ix = v1.x + u * dx;
        const iy = v1.y + u * dy;
        const distance = p.dist(px, py, ix, iy);
    
        return distance;
    }
};

new p5(sketch);

function adjustCanvasScale() {
    const parent = document.getElementById('drawcanvas');
    const canvas = parent.querySelector('canvas');
    if (canvas) {
        scale = parent.offsetWidth / canvas.offsetWidth;
        canvas.style.transform = `scale(${scale})`;
        canvas.style.transformOrigin = 'top left';
    }
}

window.addEventListener('resize', adjustCanvasScale);