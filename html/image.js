//Ludwig Krippahl,2015
//Image zooming, translating
//Acknowledgments
//  Based on code by 
//    Gavin Kistner http://phrogz.net/tmp/canvas_zoom_to_cursor.html 
//    Miguel Mota https://miguelmota.com/blog/pixelate-images-with-canvas/
//    mmansion http://jsfiddle.net/mmansion/9K5p9/

function dist2(v, w) { 
    var lx = (v.x - w.x);
	var ly = (v.y - w.y);
	return lx*lx+ly*ly;
}

function distToLine(p, v, w) {
  var l2 = dist2(v, w);

  if (l2 == 0) return dist2(p, v);
    
  var t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
  p2 = {x: v.x + t * (w.x - v.x),y: v.y + t * (w.y - v.y) };

  return Math.sqrt(dist2(p, p2));
}

var canvas = document.getElementById('zoomcanvas');
var img = document.getElementById('zoomimage')
canvas.style.cssText="image-rendering: pixelated"

window.onload = function(){		
  var ctx = canvas.getContext('2d');
  ctx.ImageSmoothingEnabled = false;
  ctx.mozImageSmoothingEnabled = false;
  ctx.msImageSmoothingEnabled = false;
  ctx.imageSmoothingEnabled = false;
  trackTransforms(ctx);
  
  function line(p1,p2,thick,color){
    ctx.beginPath();
	ctx.moveTo(p1.x,p1.y);
	ctx.lineTo(p2.x,p2.y);
	ctx.lineWidth = thick;
    ctx.strokeStyle = color;
	ctx.stroke();
	//document.getElementById('debug').innerHTML=ctx.getTransform().a;
	}
  
  function drawBox(){    
	var l_start = {x: Number(document.getElementsByName('well_x1')[0].value),
						y: Number(document.getElementsByName('well_y1')[0].value)};
	var l_end =   {x: Number(document.getElementsByName('well_x2')[0].value),
						y: Number(document.getElementsByName('well_y2')[0].value)};	
	
	line(l_start,l_end,5,'#00FFFF');
	var lvec = {x: l_start.y-l_end.y ,y: l_end.x-l_start.x};
	var lvec2 = lvec
	len = Math.sqrt(lvec.x*lvec.x+lvec.y*lvec.y);
	if (len>10){		
	    var scale = Number(document.getElementsByName('lane_length')[0].value)/len;		
		lvec2  = {x:lvec.x*scale,y:lvec.y*scale};
		p1 = {x:l_start.x+lvec2.x,y:l_start.y+lvec2.y};
		p2 = {x:l_end.x+lvec2.x,y:l_end.y+lvec2.y};
		line(l_start,p1,5,'#00FFFF');
		line(p1,p2,5,'#00FFFF');
		line(p2,l_end,5,'#00FFFF');		
	};
	if (len>10){		
	    var st_scale = Number(document.getElementsByName('lane_start')[0].value)/len;			
		lvec2  = {x:lvec.x*st_scale,y:lvec.y*st_scale};
		p1 = {x:l_start.x+lvec2.x,y:l_start.y+lvec2.y};
		p2 = {x:l_end.x+lvec2.x,y:l_end.y+lvec2.y};		
		line(p1,p2,5,'#FFFF00');		
	};
  }
  function redraw(){
    // Clear the entire canvas
    var p1 = ctx.transformedPoint(0,0);
    var p2 = ctx.transformedPoint(canvas.width,canvas.height);
    ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);
    ctx.drawImage(img,0,0);
	drawBox();
    }
  redraw();

  var lastX=canvas.width/2, lastY=canvas.height/2;
  var dragStart,dragged;
  var lastDownTarget;
  document.addEventListener('mousedown', function(event) {
        lastDownTarget = event.target;        
    }, false);

  document.addEventListener("keypress", function(evt){    
	if (lastDownTarget == canvas) {	
	evt = evt || window.event;
    var charCode = evt.keyCode || evt.which;
    var charStr = String.fromCharCode(charCode);
    if (charStr == '1'){
		document.getElementsByName('well_x1')[0].value=document.getElementById('XCOORD').innerHTML;
		document.getElementsByName('well_y1')[0].value=document.getElementById('YCOORD').innerHTML;
		};
	if (charStr == '2'){
		document.getElementsByName('well_x2')[0].value=document.getElementById('XCOORD').innerHTML;
		document.getElementsByName('well_y2')[0].value=document.getElementById('YCOORD').innerHTML;
		};
	if (charStr == '3'){	    
		var l_start = {x: Number(document.getElementsByName('well_x1')[0].value),
						y: Number(document.getElementsByName('well_y1')[0].value)};
		var l_end =   {x: Number(document.getElementsByName('well_x2')[0].value),
						y: Number(document.getElementsByName('well_y2')[0].value)};
		var point =   {x: Number(document.getElementById('XCOORD').innerHTML),
                       y:Number(document.getElementById('YCOORD').innerHTML)};
		var dist = distToLine(point,l_start,l_end);
		document.getElementsByName('lane_length')[0].value=Math.round(dist);
		};
	if (charStr == '4'){	    
		var l_start = {x: Number(document.getElementsByName('well_x1')[0].value),
						y: Number(document.getElementsByName('well_y1')[0].value)};
		var l_end =   {x: Number(document.getElementsByName('well_x2')[0].value),
						y: Number(document.getElementsByName('well_y2')[0].value)};
		var point =   {x: Number(document.getElementById('XCOORD').innerHTML),
                       y:Number(document.getElementById('YCOORD').innerHTML)};
		var dist = distToLine(point,l_start,l_end);
		document.getElementsByName('lane_start')[0].value=Math.round(dist);
		};
	};
	redraw();
	},false);
  
  canvas.addEventListener('mousedown',function(evt){
    document.body.style.mozUserSelect = document.body.style.webkitUserSelect = document.body.style.userSelect = 'none';
    lastX = evt.offsetX || (evt.pageX - canvas.offsetLeft);
    lastY = evt.offsetY || (evt.pageY - canvas.offsetTop);
    dragStart = ctx.transformedPoint(lastX,lastY);
    dragged = false;
    },false);
  canvas.addEventListener('mousemove',function(evt){
    lastX = evt.offsetX || (evt.pageX - canvas.offsetLeft);
    lastY = evt.offsetY || (evt.pageY - canvas.offsetTop);
    dragged = true;
    if (dragStart){
      var pt = ctx.transformedPoint(lastX,lastY);
      ctx.translate(pt.x-dragStart.x,pt.y-dragStart.y);
      redraw();
      }
	var p1 = ctx.transformedPoint(evt.offsetX,evt.offsetY);		
	document.getElementById('XCOORD').innerHTML = Math.round(p1.x);
	document.getElementById('YCOORD').innerHTML = Math.round(p1.y);
     
    },false);
  canvas.addEventListener('mouseup',function(evt){
    dragStart = null;
    if (!dragged) zoom(evt.shiftKey ? -1 : 1 );
    },false);

  var scaleFactor = 1.2;
  
  var zoom = function(clicks){
    var pt = ctx.transformedPoint(lastX,lastY);
    ctx.translate(pt.x,pt.y);
    var factor = Math.pow(scaleFactor,clicks);
    ctx.scale(factor,factor);
    ctx.translate(-pt.x,-pt.y);
    redraw();
    }

  var handleScroll = function(evt){
    var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
    if (delta) zoom(delta);
      return evt.preventDefault() && false;
      };
  
  canvas.addEventListener('DOMMouseScroll',handleScroll,false);
  canvas.addEventListener('mousewheel',handleScroll,false);
  };


// Adds ctx.getTransform() - returns an SVGMatrix
// Adds ctx.transformedPoint(x,y) - returns an SVGPoint
function trackTransforms(ctx){
  var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
  var xform = svg.createSVGMatrix();
  ctx.getTransform = function(){ return xform; };

  var savedTransforms = [];
  var save = ctx.save;
  ctx.save = function(){
  savedTransforms.push(xform.translate(0,0));
  return save.call(ctx);
  };

  var restore = ctx.restore;
  ctx.restore = function(){
    xform = savedTransforms.pop();
    return restore.call(ctx);
    };

  var scale = ctx.scale;
  ctx.scale = function(sx,sy){
    xform = xform.scaleNonUniform(sx,sy);
    return scale.call(ctx,sx,sy);
    };

  var rotate = ctx.rotate;
  ctx.rotate = function(radians){
    xform = xform.rotate(radians*180/Math.PI);
    return rotate.call(ctx,radians);
    };

  var translate = ctx.translate;
  ctx.translate = function(dx,dy){
    xform = xform.translate(dx,dy);
    return translate.call(ctx,dx,dy);
    };

  var transform = ctx.transform;
  ctx.transform = function(a,b,c,d,e,f){
    var m2 = svg.createSVGMatrix();
    m2.a=a; m2.b=b; m2.c=c; m2.d=d; m2.e=e; m2.f=f;
    xform = xform.multiply(m2);
    return transform.call(ctx,a,b,c,d,e,f);
    };

  var setTransform = ctx.setTransform;
  ctx.setTransform = function(a,b,c,d,e,f){
    xform.a = a;
    xform.b = b;
    xform.c = c;
    xform.d = d;
    xform.e = e;
    xform.f = f;
    return setTransform.call(ctx,a,b,c,d,e,f);
    };

  var pt  = svg.createSVGPoint();
  ctx.transformedPoint = function(x,y){
    pt.x=x; pt.y=y;
    return pt.matrixTransform(xform.inverse());
    }
  ctx.transformedPointBack = function(x,y){
    pt.x=x; pt.y=y;
    return pt.matrixTransform(xform);
    }
  }
 
