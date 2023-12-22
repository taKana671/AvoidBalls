#version 300 es

precision highp float;
uniform vec2 u_resolution;
uniform float osg_FrameTime;
uniform sampler2D noise;
uniform sampler2D p3d_Texture0;
// uniform sampler2D Heightmap;
// uniform sampler2D surface;

in vec2 texcoord;
out vec4 fragColor;


void main() {
    vec2 uv = (2. * gl_FragCoord.xy - u_resolution.xy) / u_resolution.y;
    // vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    // vec2 uv = gl_FragCoord.xy / u_resolution.x * 2.0 - 1.0;
    vec2 wrap_uv = 2.0 * uv;

    float d = length(wrap_uv);
    vec2 st =  wrap_uv * 0.1 + 0.2 * vec2(cos(0.071 * osg_FrameTime * 2.0 + d), sin(0.073 * osg_FrameTime * 2.0 - d));

    vec3 warped_col = texture(noise, st).xyz * 2.0;
    float w = max(warped_col.r, 0.85);
    
    vec2 offset = 0.01 * cos(warped_col.rg * 3.14159);
    vec3 col = texture(p3d_Texture0, uv + offset).rgb * vec3(0.8, 0.8, 1.5);
    col *= w * 1.2;
    
    
    fragColor = vec4(mix(col, texture(p3d_Texture0, uv + offset).rgb, 0.5),  0.6);


    // vec3 col1 = texture(Heightmap, texcoord4).rgb;
    // vec2 wrap_uv = 2.0 * uv;
    // float d = length(wrap_uv);
    // vec2 st =  wrap_uv *0.1 + 0.2 * vec2(cos(0.071 * osg_FrameTime * 2.0 + d), sin(0.073 * osg_FrameTime * 2.0 - d));
    // vec3 warped_col = texture(normal_map, st).xyz * 2.0;
    // float w = max(warped_col.r, 0.85);
    // vec2 offset = 0.01 * cos(warped_col.rg * 3.14159);
    // vec3 col = texture(normal_map, uv + offset).rgb * vec4(0.8, 0.8, 1.5);
    // col *= w * 1.2;

    // col = vec4(mix(col, texture(normal_map, uv + offset ).rgb, 0.5),  0.5);


    // fragColor = tex0 * w0 + tex1 * w1 + tex2 * w2 + tex3 * w3;
    // if (col1.x == 0.0) {
    //     // vec3 col = texture(normal_map, uv + offset).rgb * vec3(0.6, 0.8, 0.8);
    //     vec3 col = texture(river, uv).rgb;        
    //     // col *= w*1.2;
    //     // fragColor = vec4(mix(col, texture(p3d_Texture0, uv + offset).rgb, 0.5),  1.0);
    //     // fragColor = vec4(mix(col, fragColor.rgb, 0.5),  1.0);
    //     fragColor = vec4(mix(col, fragColor.rgb, 0.5),  1.0);

    // } else {
    //     fragColor = tex0 * w0 + tex1 * w1 + tex2 * w2 + tex3 * w3;
    // }



    // if (col1 == vec3(0.0, 0.0, 0.0)) {
    //     vec3 col = texture(normal_map, uv + offset).rgb * vec3(0.8, 0.8, 0.8);
    //     col *= w*1.2;
    //     // fragColor = vec4(mix(col, texture(p3d_Texture0, uv + offset).rgb, 0.5),  1.0);
    //     fragColor = vec4(mix(col, fragColor.rgb, 0.5),  1.0);
    // } else {
    //     fragColor = tex0 * w0 + tex1 * w1 + tex2 * w2 + tex3 * w3;
    // }


}

