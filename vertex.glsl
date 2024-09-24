in vec2 pos;
out vec2 uv;

uniform vec2 drawSize;      // absolute region coords
uniform vec2 regionSize;    // absolute region coords
uniform vec4 cropArea;      // normalized image-space coords
uniform vec2 drawPos;       // normalized region coords

void main() {
    vec2 croppedPos; 
    croppedPos.x = (float(pos.x == 0) * cropArea.x) + (float(pos.x == 1) * cropArea.z);
    croppedPos.y = (float(pos.y == 0) * cropArea.y) + (float(pos.y == 1) * cropArea.w);
    uv = croppedPos; 

    float x = drawSize.x * croppedPos.x / regionSize.x + drawPos.x;
    float y = drawSize.y * croppedPos.y / regionSize.y + drawPos.y;
    x = 2 * x - 1;
    y = 2 * y - 1;

    gl_Position = vec4(x, y, 0.0, 1.0);
}