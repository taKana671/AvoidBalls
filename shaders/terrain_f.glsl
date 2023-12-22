#version 300 es
precision highp float;

uniform float tex_ScaleFactor0;
uniform float tex_ScaleFactor1;
uniform float tex_ScaleFactor2;
uniform float tex_ScaleFactor3;

uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;
uniform sampler2D p3d_Texture3;

in vec2 texcoord0;
in vec2 texcoord1;
in vec2 texcoord2;
in vec2 texcoord3;
in vec4 vertex;
out vec4 fragColor;


float computeWeight(float min_z, float max_z, vec4 vertex){
    float region = max_z - min_z;
    return max(0.0, (region - abs(vertex.z - max_z)) / region);
}

void main() {
    vec4 tex0 = texture(p3d_Texture0, texcoord0.st * tex_ScaleFactor0).rgba;
    vec4 tex1 = texture(p3d_Texture1, texcoord1.st * tex_ScaleFactor1).rgba;
    vec4 tex2 = texture(p3d_Texture2, texcoord2.st * tex_ScaleFactor2).rgba;
    vec4 tex3 = texture(p3d_Texture3, texcoord3.st * tex_ScaleFactor3).rgba;

    float scale = 500.0;
    float min_z = 0.0;
    float max_z = 0.0;
    float w0 = 0.0;
    float w1 = 0.0;
    float w2 = 0.0;
    float w3 = 0.0;

    // stone
    min_z = -100.0/scale;
    max_z = 50.0/scale;
    // min_z = -100.0/scale;
    // max_z = 0.0/scale;
    w0 = computeWeight(min_z, max_z, vertex);

    // glass
    min_z = 51.0/scale;
    max_z = 200.0/scale;
    w1 = computeWeight(min_z, max_z, vertex);

    // red_ground
    min_z = 201.0/scale;
    max_z = 300.0/scale;
    // min_z = 101.0/scale;
    // max_z = 200.0/scale;
    w2 = computeWeight(min_z, max_z, vertex);

    // dark_green
    min_z = 301.0/scale;
    max_z = 500.0/scale;
    // min_z = 201.0/scale;
    // max_z = 300.0/scale;
    w3 = computeWeight(min_z, max_z, vertex);


    fragColor = tex0 * w0 + tex1 * w1 + tex2 * w2 + tex3 * w3;
}

