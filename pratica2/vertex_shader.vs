#version 330 core

attribute vec3 position;
attribute vec2 texture_coord;
varying vec2 coordenadasTextura;
		
uniform mat4 mat_transform;        

void main(){
	gl_Position = mat_transform * vec4(position,1.0);
	coordenadasTextura = vec2(texture_coord);
}