#version 300 es

precision highp float;
uniform vec2 u_resolution;
uniform float osg_FrameTime;
uniform sampler2D noise;
uniform sampler2D p3d_Texture0;

// in vec2 texcoord0;
out vec4 fragColor;


void main() {
    // vec2 uv = (2. * gl_FragCoord.xy - u_resolution.xy) / min(u_resolution.y, u_resolution.x);
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    vec2 wrap_uv = 2.0 * uv;

    float d = length(wrap_uv);
    vec2 st =  wrap_uv * 0.1 + 0.2 * vec2(cos(0.071 * osg_FrameTime * 2.0 + d), sin(0.073 * osg_FrameTime * 2.0 - d));

    vec3 warped_col = texture(noise, st).xyz * 2.0;
    float w = max(warped_col.r, 0.85);
    vec2 offset = 0.01 * cos(warped_col.rg * 3.14159);
    vec3 col = texture(p3d_Texture0, uv + offset).rgb * vec3(0.8, 0.8, 1.5);
   
    fragColor = vec4(mix(col, texture(p3d_Texture0, uv + offset).rgb, 0.5),  0.6);
}