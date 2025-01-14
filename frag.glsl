in vec2 uv;
out vec4 fragColor;

uniform sampler2D image;

void main() {
    fragColor = texture(image, uv);
}
