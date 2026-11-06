async ({storage})=>{
 const source=await fetch('/src/rendering/createRenderer.ts').then(r=>r.text());
 const T=await import(source.match(/from ['"]([^'"]*three\.js[^'"]*)['"]/)[1]);
 const {createRenderer}=await import('/src/rendering/createRenderer.ts');
 const scene=new T.Scene(),camera=new T.OrthographicCamera(-1,1,1,-1,.1,10);camera.position.z=1;
 const hex=['#030609','#0a0f17','#124b3c','#58a7b5','#ffb6d5','#e5eacb','#ffffff','#000000','#2b557c','#b3d3df','#b9d964','#117356','#183d35','#728f96','#f3ebc2','#dba2e8'];
 const geometry=new T.PlaneGeometry(.5,.5),materials=[];
 hex.forEach((color,i)=>{
  const material=new T.MeshBasicMaterial({color,toneMapped:false});materials.push(material);
  const mesh=new T.Mesh(geometry,material);mesh.position.set(-.75+(i%4)*.5,.75-Math.floor(i/4)*.5,0);scene.add(mesh);
 });
 const view=createRenderer(document.querySelector('#capture'),'native',()=>{},{resolution:320,finish:'clean',storage});
 view.setAnimating(false);view.start(scene,camera);
 window.__test={T,view,scene,camera,hex,geometry,materials,checker(){
  scene.clear();const g=new T.PlaneGeometry(2,2);const m=new T.ShaderMaterial({toneMapped:false,
   vertexShader:'varying vec2 v;void main(){v=uv;gl_Position=vec4(position.xy,0.,1.);}',
   fragmentShader:'varying vec2 v;void main(){vec2 p=floor(v*320.);float c=mod(p.x+p.y,2.);gl_FragColor=vec4(vec3(c),1.);}'});
  this.checkerGeometry=g;this.checkerMaterial=m;scene.add(new T.Mesh(g,m));view.renderOnce();
 },dispose(){view.dispose();geometry.dispose();materials.forEach(m=>m.dispose());this.checkerGeometry?.dispose();this.checkerMaterial?.dispose();}};
 return hex;
}
