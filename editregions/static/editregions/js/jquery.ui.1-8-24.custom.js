/*!
 * jQuery UI 1.8.24
 *
 * Copyright 2012, AUTHORS.txt (http://jqueryui.com/about)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * http://docs.jquery.com/UI
 */
(function(a,d){a.ui=a.ui||{};
if(a.ui.version){return;}a.extend(a.ui,{version:"1.8.24",keyCode:{ALT:18,BACKSPACE:8,CAPS_LOCK:20,COMMA:188,COMMAND:91,COMMAND_LEFT:91,COMMAND_RIGHT:93,CONTROL:17,DELETE:46,DOWN:40,END:35,ENTER:13,ESCAPE:27,HOME:36,INSERT:45,LEFT:37,MENU:93,NUMPAD_ADD:107,NUMPAD_DECIMAL:110,NUMPAD_DIVIDE:111,NUMPAD_ENTER:108,NUMPAD_MULTIPLY:106,NUMPAD_SUBTRACT:109,PAGE_DOWN:34,PAGE_UP:33,PERIOD:190,RIGHT:39,SHIFT:16,SPACE:32,TAB:9,UP:38,WINDOWS:91}});
a.fn.extend({propAttr:a.fn.prop||a.fn.attr,_focus:a.fn.focus,focus:function(e,f){return typeof e==="number"?this.each(function(){var g=this;
setTimeout(function(){a(g).focus();if(f){f.call(g);}},e);}):this._focus.apply(this,arguments);
},scrollParent:function(){var e;if((a.browser.msie&&(/(static|relative)/).test(this.css("position")))||(/absolute/).test(this.css("position"))){e=this.parents().filter(function(){return(/(relative|absolute|fixed)/).test(a.curCSS(this,"position",1))&&(/(auto|scroll)/).test(a.curCSS(this,"overflow",1)+a.curCSS(this,"overflow-y",1)+a.curCSS(this,"overflow-x",1));
}).eq(0);}else{e=this.parents().filter(function(){return(/(auto|scroll)/).test(a.curCSS(this,"overflow",1)+a.curCSS(this,"overflow-y",1)+a.curCSS(this,"overflow-x",1));
}).eq(0);}return(/fixed/).test(this.css("position"))||!e.length?a(document):e;},zIndex:function(h){if(h!==d){return this.css("zIndex",h);
}if(this.length){var f=a(this[0]),e,g;while(f.length&&f[0]!==document){e=f.css("position");
if(e==="absolute"||e==="relative"||e==="fixed"){g=parseInt(f.css("zIndex"),10);if(!isNaN(g)&&g!==0){return g;
}}f=f.parent();}}return 0;},disableSelection:function(){return this.bind((a.support.selectstart?"selectstart":"mousedown")+".ui-disableSelection",function(e){e.preventDefault();
});},enableSelection:function(){return this.unbind(".ui-disableSelection");}});if(!a("<a>").outerWidth(1).jquery){a.each(["Width","Height"],function(g,e){var f=e==="Width"?["Left","Right"]:["Top","Bottom"],h=e.toLowerCase(),k={innerWidth:a.fn.innerWidth,innerHeight:a.fn.innerHeight,outerWidth:a.fn.outerWidth,outerHeight:a.fn.outerHeight};
function j(m,l,i,n){a.each(f,function(){l-=parseFloat(a.curCSS(m,"padding"+this,true))||0;
if(i){l-=parseFloat(a.curCSS(m,"border"+this+"Width",true))||0;}if(n){l-=parseFloat(a.curCSS(m,"margin"+this,true))||0;
}});return l;}a.fn["inner"+e]=function(i){if(i===d){return k["inner"+e].call(this);
}return this.each(function(){a(this).css(h,j(this,i)+"px");});};a.fn["outer"+e]=function(i,l){if(typeof i!=="number"){return k["outer"+e].call(this,i);
}return this.each(function(){a(this).css(h,j(this,i,true,l)+"px");});};});}function c(g,e){var j=g.nodeName.toLowerCase();
if("area"===j){var i=g.parentNode,h=i.name,f;if(!g.href||!h||i.nodeName.toLowerCase()!=="map"){return false;
}f=a("img[usemap=#"+h+"]")[0];return !!f&&b(f);}return(/input|select|textarea|button|object/.test(j)?!g.disabled:"a"==j?g.href||e:e)&&b(g);
}function b(e){return !a(e).parents().andSelf().filter(function(){return a.curCSS(this,"visibility")==="hidden"||a.expr.filters.hidden(this);
}).length;}a.extend(a.expr[":"],{data:a.expr.createPseudo?a.expr.createPseudo(function(e){return function(f){return !!a.data(f,e);
};}):function(g,f,e){return !!a.data(g,e[3]);},focusable:function(e){return c(e,!isNaN(a.attr(e,"tabindex")));
},tabbable:function(g){var e=a.attr(g,"tabindex"),f=isNaN(e);return(f||e>=0)&&c(g,!f);
}});a(function(){var e=document.body,f=e.appendChild(f=document.createElement("div"));
f.offsetHeight;a.extend(f.style,{minHeight:"100px",height:"auto",padding:0,borderWidth:0});
a.support.minHeight=f.offsetHeight===100;a.support.selectstart="onselectstart" in f;
e.removeChild(f).style.display="none";});if(!a.curCSS){a.curCSS=a.css;}a.extend(a.ui,{plugin:{add:function(f,g,j){var h=a.ui[f].prototype;
for(var e in j){h.plugins[e]=h.plugins[e]||[];h.plugins[e].push([g,j[e]]);}},call:function(e,g,f){var j=e.plugins[g];
if(!j||!e.element[0].parentNode){return;}for(var h=0;h<j.length;h++){if(e.options[j[h][0]]){j[h][1].apply(e.element,f);
}}}},contains:function(f,e){return document.compareDocumentPosition?f.compareDocumentPosition(e)&16:f!==e&&f.contains(e);
},hasScroll:function(h,f){if(a(h).css("overflow")==="hidden"){return false;}var e=(f&&f==="left")?"scrollLeft":"scrollTop",g=false;
if(h[e]>0){return true;}h[e]=1;g=(h[e]>0);h[e]=0;return g;},isOverAxis:function(f,e,g){return(f>e)&&(f<(e+g));
},isOver:function(j,f,i,h,e,g){return a.ui.isOverAxis(j,i,e)&&a.ui.isOverAxis(f,h,g);
}});})(jQuery);
/*!
 * jQuery UI Widget 1.8.24
 *
 * Copyright 2012, AUTHORS.txt (http://jqueryui.com/about)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * http://docs.jquery.com/UI/Widget
 */
(function(b,d){if(b.cleanData){var c=b.cleanData;
b.cleanData=function(f){for(var g=0,h;(h=f[g])!=null;g++){try{b(h).triggerHandler("remove");
}catch(j){}}c(f);};}else{var a=b.fn.remove;b.fn.remove=function(e,f){return this.each(function(){if(!f){if(!e||b.filter(e,[this]).length){b("*",this).add([this]).each(function(){try{b(this).triggerHandler("remove");
}catch(g){}});}}return a.call(b(this),e,f);});};}b.widget=function(f,h,e){var g=f.split(".")[0],j;
f=f.split(".")[1];j=g+"-"+f;if(!e){e=h;h=b.Widget;}b.expr[":"][j]=function(k){return !!b.data(k,f);
};b[g]=b[g]||{};b[g][f]=function(k,l){if(arguments.length){this._createWidget(k,l);
}};var i=new h();i.options=b.extend(true,{},i.options);b[g][f].prototype=b.extend(true,i,{namespace:g,widgetName:f,widgetEventPrefix:b[g][f].prototype.widgetEventPrefix||f,widgetBaseClass:j},e);
b.widget.bridge(f,b[g][f]);};b.widget.bridge=function(f,e){b.fn[f]=function(i){var g=typeof i==="string",h=Array.prototype.slice.call(arguments,1),j=this;
i=!g&&h.length?b.extend.apply(null,[true,i].concat(h)):i;if(g&&i.charAt(0)==="_"){return j;
}if(g){this.each(function(){var k=b.data(this,f),l=k&&b.isFunction(k[i])?k[i].apply(k,h):k;
if(l!==k&&l!==d){j=l;return false;}});}else{this.each(function(){var k=b.data(this,f);
if(k){k.option(i||{})._init();}else{b.data(this,f,new e(i,this));}});}return j;};
};b.Widget=function(e,f){if(arguments.length){this._createWidget(e,f);}};b.Widget.prototype={widgetName:"widget",widgetEventPrefix:"",options:{disabled:false},_createWidget:function(f,g){b.data(g,this.widgetName,this);
this.element=b(g);this.options=b.extend(true,{},this.options,this._getCreateOptions(),f);
var e=this;this.element.bind("remove."+this.widgetName,function(){e.destroy();});
this._create();this._trigger("create");this._init();},_getCreateOptions:function(){return b.metadata&&b.metadata.get(this.element[0])[this.widgetName];
},_create:function(){},_init:function(){},destroy:function(){this.element.unbind("."+this.widgetName).removeData(this.widgetName);
this.widget().unbind("."+this.widgetName).removeAttr("aria-disabled").removeClass(this.widgetBaseClass+"-disabled ui-state-disabled");
},widget:function(){return this.element;},option:function(f,g){var e=f;if(arguments.length===0){return b.extend({},this.options);
}if(typeof f==="string"){if(g===d){return this.options[f];}e={};e[f]=g;}this._setOptions(e);
return this;},_setOptions:function(f){var e=this;b.each(f,function(g,h){e._setOption(g,h);
});return this;},_setOption:function(e,f){this.options[e]=f;if(e==="disabled"){this.widget()[f?"addClass":"removeClass"](this.widgetBaseClass+"-disabled ui-state-disabled").attr("aria-disabled",f);
}return this;},enable:function(){return this._setOption("disabled",false);},disable:function(){return this._setOption("disabled",true);
},_trigger:function(e,f,g){var j,i,h=this.options[e];g=g||{};f=b.Event(f);f.type=(e===this.widgetEventPrefix?e:this.widgetEventPrefix+e).toLowerCase();
f.target=this.element[0];i=f.originalEvent;if(i){for(j in i){if(!(j in f)){f[j]=i[j];
}}}this.element.trigger(f,g);return !(b.isFunction(h)&&h.call(this.element[0],f,g)===false||f.isDefaultPrevented());
}};})(jQuery);
/*!
 * jQuery UI Mouse 1.8.24
 *
 * Copyright 2012, AUTHORS.txt (http://jqueryui.com/about)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * http://docs.jquery.com/UI/Mouse
 *
 * Depends:
 *	jquery.ui.widget.js
 */
(function(b,c){var a=false;
b(document).mouseup(function(d){a=false;});b.widget("ui.mouse",{options:{cancel:":input,option",distance:1,delay:0},_mouseInit:function(){var d=this;
this.element.bind("mousedown."+this.widgetName,function(e){return d._mouseDown(e);
}).bind("click."+this.widgetName,function(e){if(true===b.data(e.target,d.widgetName+".preventClickEvent")){b.removeData(e.target,d.widgetName+".preventClickEvent");
e.stopImmediatePropagation();return false;}});this.started=false;},_mouseDestroy:function(){this.element.unbind("."+this.widgetName);
if(this._mouseMoveDelegate){b(document).unbind("mousemove."+this.widgetName,this._mouseMoveDelegate).unbind("mouseup."+this.widgetName,this._mouseUpDelegate);
}},_mouseDown:function(f){if(a){return;}(this._mouseStarted&&this._mouseUp(f));this._mouseDownEvent=f;
var e=this,g=(f.which==1),d=(typeof this.options.cancel=="string"&&f.target.nodeName?b(f.target).closest(this.options.cancel).length:false);
if(!g||d||!this._mouseCapture(f)){return true;}this.mouseDelayMet=!this.options.delay;
if(!this.mouseDelayMet){this._mouseDelayTimer=setTimeout(function(){e.mouseDelayMet=true;
},this.options.delay);}if(this._mouseDistanceMet(f)&&this._mouseDelayMet(f)){this._mouseStarted=(this._mouseStart(f)!==false);
if(!this._mouseStarted){f.preventDefault();return true;}}if(true===b.data(f.target,this.widgetName+".preventClickEvent")){b.removeData(f.target,this.widgetName+".preventClickEvent");
}this._mouseMoveDelegate=function(h){return e._mouseMove(h);};this._mouseUpDelegate=function(h){return e._mouseUp(h);
};b(document).bind("mousemove."+this.widgetName,this._mouseMoveDelegate).bind("mouseup."+this.widgetName,this._mouseUpDelegate);
f.preventDefault();a=true;return true;},_mouseMove:function(d){if(b.browser.msie&&!(document.documentMode>=9)&&!d.button){return this._mouseUp(d);
}if(this._mouseStarted){this._mouseDrag(d);return d.preventDefault();}if(this._mouseDistanceMet(d)&&this._mouseDelayMet(d)){this._mouseStarted=(this._mouseStart(this._mouseDownEvent,d)!==false);
(this._mouseStarted?this._mouseDrag(d):this._mouseUp(d));}return !this._mouseStarted;
},_mouseUp:function(d){b(document).unbind("mousemove."+this.widgetName,this._mouseMoveDelegate).unbind("mouseup."+this.widgetName,this._mouseUpDelegate);
if(this._mouseStarted){this._mouseStarted=false;if(d.target==this._mouseDownEvent.target){b.data(d.target,this.widgetName+".preventClickEvent",true);
}this._mouseStop(d);}return false;},_mouseDistanceMet:function(d){return(Math.max(Math.abs(this._mouseDownEvent.pageX-d.pageX),Math.abs(this._mouseDownEvent.pageY-d.pageY))>=this.options.distance);
},_mouseDelayMet:function(d){return this.mouseDelayMet;},_mouseStart:function(d){},_mouseDrag:function(d){},_mouseStop:function(d){},_mouseCapture:function(d){return true;
}});})(jQuery);
/*!
 * jQuery UI Touch Punch 0.2.2
 *
 * Copyright 2011, Dave Furfero
 * Dual licensed under the MIT or GPL Version 2 licenses.
 *
 * Depends:
 *  jquery.ui.widget.js
 *  jquery.ui.mouse.js
 */
(function(b){b.support.touch="ontouchend" in document;
if(!b.support.touch){return;}var c=b.ui.mouse.prototype,e=c._mouseInit,a;function d(g,h){if(g.originalEvent.touches.length>1){return;
}g.preventDefault();var i=g.originalEvent.changedTouches[0],f=document.createEvent("MouseEvents");
f.initMouseEvent(h,true,true,window,1,i.screenX,i.screenY,i.clientX,i.clientY,false,false,false,false,0,null);
g.target.dispatchEvent(f);}c._touchStart=function(g){var f=this;if(a||!f._mouseCapture(g.originalEvent.changedTouches[0])){return;
}a=true;f._touchMoved=false;d(g,"mouseover");d(g,"mousemove");d(g,"mousedown");};
c._touchMove=function(f){if(!a){return;}this._touchMoved=true;d(f,"mousemove");};
c._touchEnd=function(f){if(!a){return;}d(f,"mouseup");d(f,"mouseout");if(!this._touchMoved){d(f,"click");
}a=false;};c._mouseInit=function(){var f=this;f.element.bind("touchstart",b.proxy(f,"_touchStart")).bind("touchmove",b.proxy(f,"_touchMove")).bind("touchend",b.proxy(f,"_touchEnd"));
e.call(f);};})(jQuery);
/*!
 * jQuery UI Sortable 1.8.24
 *
 * Copyright 2012, AUTHORS.txt (http://jqueryui.com/about)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * http://docs.jquery.com/UI/Sortables
 *
 * Depends:
 *	jquery.ui.core.js
 *	jquery.ui.mouse.js
 *	jquery.ui.widget.js
 */
(function(a,b){a.widget("ui.sortable",a.ui.mouse,{widgetEventPrefix:"sort",ready:false,options:{appendTo:"parent",axis:false,connectWith:false,containment:false,cursor:"auto",cursorAt:false,dropOnEmpty:true,forcePlaceholderSize:false,forceHelperSize:false,grid:false,handle:false,helper:"original",items:"> *",opacity:false,placeholder:false,revert:false,scroll:true,scrollSensitivity:20,scrollSpeed:20,scope:"default",tolerance:"intersect",zIndex:1000},_create:function(){var c=this.options;
this.containerCache={};this.element.addClass("ui-sortable");this.refresh();this.floating=this.items.length?c.axis==="x"||(/left|right/).test(this.items[0].item.css("float"))||(/inline|table-cell/).test(this.items[0].item.css("display")):false;
this.offset=this.element.offset();this._mouseInit();this.ready=true;},destroy:function(){a.Widget.prototype.destroy.call(this);
this.element.removeClass("ui-sortable ui-sortable-disabled");this._mouseDestroy();
for(var c=this.items.length-1;c>=0;c--){this.items[c].item.removeData(this.widgetName+"-item");
}return this;},_setOption:function(c,d){if(c==="disabled"){this.options[c]=d;this.widget()[d?"addClass":"removeClass"]("ui-sortable-disabled");
}else{a.Widget.prototype._setOption.apply(this,arguments);}},_mouseCapture:function(g,h){var f=this;
if(this.reverting){return false;}if(this.options.disabled||this.options.type=="static"){return false;
}this._refreshItems(g);var e=null,d=this,c=a(g.target).parents().each(function(){if(a.data(this,f.widgetName+"-item")==d){e=a(this);
return false;}});if(a.data(g.target,f.widgetName+"-item")==d){e=a(g.target);}if(!e){return false;
}if(this.options.handle&&!h){var i=false;a(this.options.handle,e).find("*").andSelf().each(function(){if(this==g.target){i=true;
}});if(!i){return false;}}this.currentItem=e;this._removeCurrentsFromItems();return true;
},_mouseStart:function(f,g,c){var h=this.options,d=this;this.currentContainer=this;
this.refreshPositions();this.helper=this._createHelper(f);this._cacheHelperProportions();
this._cacheMargins();this.scrollParent=this.helper.scrollParent();this.offset=this.currentItem.offset();
this.offset={top:this.offset.top-this.margins.top,left:this.offset.left-this.margins.left};
a.extend(this.offset,{click:{left:f.pageX-this.offset.left,top:f.pageY-this.offset.top},parent:this._getParentOffset(),relative:this._getRelativeOffset()});
this.helper.css("position","absolute");this.cssPosition=this.helper.css("position");
this.originalPosition=this._generatePosition(f);this.originalPageX=f.pageX;this.originalPageY=f.pageY;
(h.cursorAt&&this._adjustOffsetFromHelper(h.cursorAt));this.domPosition={prev:this.currentItem.prev()[0],parent:this.currentItem.parent()[0]};
if(this.helper[0]!=this.currentItem[0]){this.currentItem.hide();}this._createPlaceholder();
if(h.containment){this._setContainment();}if(h.cursor){if(a("body").css("cursor")){this._storedCursor=a("body").css("cursor");
}a("body").css("cursor",h.cursor);}if(h.opacity){if(this.helper.css("opacity")){this._storedOpacity=this.helper.css("opacity");
}this.helper.css("opacity",h.opacity);}if(h.zIndex){if(this.helper.css("zIndex")){this._storedZIndex=this.helper.css("zIndex");
}this.helper.css("zIndex",h.zIndex);}if(this.scrollParent[0]!=document&&this.scrollParent[0].tagName!="HTML"){this.overflowOffset=this.scrollParent.offset();
}this._trigger("start",f,this._uiHash());if(!this._preserveHelperProportions){this._cacheHelperProportions();
}if(!c){for(var e=this.containers.length-1;e>=0;e--){this.containers[e]._trigger("activate",f,d._uiHash(this));
}}if(a.ui.ddmanager){a.ui.ddmanager.current=this;}if(a.ui.ddmanager&&!h.dropBehaviour){a.ui.ddmanager.prepareOffsets(this,f);
}this.dragging=true;this.helper.addClass("ui-sortable-helper");this._mouseDrag(f);
return true;},_mouseDrag:function(g){this.position=this._generatePosition(g);this.positionAbs=this._convertPositionTo("absolute");
if(!this.lastPositionAbs){this.lastPositionAbs=this.positionAbs;}if(this.options.scroll){var h=this.options,c=false;
if(this.scrollParent[0]!=document&&this.scrollParent[0].tagName!="HTML"){if((this.overflowOffset.top+this.scrollParent[0].offsetHeight)-g.pageY<h.scrollSensitivity){this.scrollParent[0].scrollTop=c=this.scrollParent[0].scrollTop+h.scrollSpeed;
}else{if(g.pageY-this.overflowOffset.top<h.scrollSensitivity){this.scrollParent[0].scrollTop=c=this.scrollParent[0].scrollTop-h.scrollSpeed;
}}if((this.overflowOffset.left+this.scrollParent[0].offsetWidth)-g.pageX<h.scrollSensitivity){this.scrollParent[0].scrollLeft=c=this.scrollParent[0].scrollLeft+h.scrollSpeed;
}else{if(g.pageX-this.overflowOffset.left<h.scrollSensitivity){this.scrollParent[0].scrollLeft=c=this.scrollParent[0].scrollLeft-h.scrollSpeed;
}}}else{if(g.pageY-a(document).scrollTop()<h.scrollSensitivity){c=a(document).scrollTop(a(document).scrollTop()-h.scrollSpeed);
}else{if(a(window).height()-(g.pageY-a(document).scrollTop())<h.scrollSensitivity){c=a(document).scrollTop(a(document).scrollTop()+h.scrollSpeed);
}}if(g.pageX-a(document).scrollLeft()<h.scrollSensitivity){c=a(document).scrollLeft(a(document).scrollLeft()-h.scrollSpeed);
}else{if(a(window).width()-(g.pageX-a(document).scrollLeft())<h.scrollSensitivity){c=a(document).scrollLeft(a(document).scrollLeft()+h.scrollSpeed);
}}}if(c!==false&&a.ui.ddmanager&&!h.dropBehaviour){a.ui.ddmanager.prepareOffsets(this,g);
}}this.positionAbs=this._convertPositionTo("absolute");if(!this.options.axis||this.options.axis!="y"){this.helper[0].style.left=this.position.left+"px";
}if(!this.options.axis||this.options.axis!="x"){this.helper[0].style.top=this.position.top+"px";
}for(var e=this.items.length-1;e>=0;e--){var f=this.items[e],d=f.item[0],j=this._intersectsWithPointer(f);
if(!j){continue;}if(f.instance!==this.currentContainer){continue;}if(d!=this.currentItem[0]&&this.placeholder[j==1?"next":"prev"]()[0]!=d&&!a.ui.contains(this.placeholder[0],d)&&(this.options.type=="semi-dynamic"?!a.ui.contains(this.element[0],d):true)){this.direction=j==1?"down":"up";
if(this.options.tolerance=="pointer"||this._intersectsWithSides(f)){this._rearrange(g,f);
}else{break;}this._trigger("change",g,this._uiHash());break;}}this._contactContainers(g);
if(a.ui.ddmanager){a.ui.ddmanager.drag(this,g);}this._trigger("sort",g,this._uiHash());
this.lastPositionAbs=this.positionAbs;return false;},_mouseStop:function(d,e){if(!d){return;
}if(a.ui.ddmanager&&!this.options.dropBehaviour){a.ui.ddmanager.drop(this,d);}if(this.options.revert){var c=this;
var f=c.placeholder.offset();c.reverting=true;a(this.helper).animate({left:f.left-this.offset.parent.left-c.margins.left+(this.offsetParent[0]==document.body?0:this.offsetParent[0].scrollLeft),top:f.top-this.offset.parent.top-c.margins.top+(this.offsetParent[0]==document.body?0:this.offsetParent[0].scrollTop)},parseInt(this.options.revert,10)||500,function(){c._clear(d);
});}else{this._clear(d,e);}return false;},cancel:function(){var c=this;if(this.dragging){this._mouseUp({target:null});
if(this.options.helper=="original"){this.currentItem.css(this._storedCSS).removeClass("ui-sortable-helper");
}else{this.currentItem.show();}for(var d=this.containers.length-1;d>=0;d--){this.containers[d]._trigger("deactivate",null,c._uiHash(this));
if(this.containers[d].containerCache.over){this.containers[d]._trigger("out",null,c._uiHash(this));
this.containers[d].containerCache.over=0;}}}if(this.placeholder){if(this.placeholder[0].parentNode){this.placeholder[0].parentNode.removeChild(this.placeholder[0]);
}if(this.options.helper!="original"&&this.helper&&this.helper[0].parentNode){this.helper.remove();
}a.extend(this,{helper:null,dragging:false,reverting:false,_noFinalSort:null});if(this.domPosition.prev){a(this.domPosition.prev).after(this.currentItem);
}else{a(this.domPosition.parent).prepend(this.currentItem);}}return this;},serialize:function(e){var c=this._getItemsAsjQuery(e&&e.connected);
var d=[];e=e||{};a(c).each(function(){var f=(a(e.item||this).attr(e.attribute||"id")||"").match(e.expression||(/(.+)[-=_](.+)/));
if(f){d.push((e.key||f[1]+"[]")+"="+(e.key&&e.expression?f[1]:f[2]));}});if(!d.length&&e.key){d.push(e.key+"=");
}return d.join("&");},toArray:function(e){var c=this._getItemsAsjQuery(e&&e.connected);
var d=[];e=e||{};c.each(function(){d.push(a(e.item||this).attr(e.attribute||"id")||"");
});return d;},_intersectsWith:function(m){var e=this.positionAbs.left,d=e+this.helperProportions.width,k=this.positionAbs.top,j=k+this.helperProportions.height;
var f=m.left,c=f+m.width,n=m.top,i=n+m.height;var o=this.offset.click.top,h=this.offset.click.left;
var g=(k+o)>n&&(k+o)<i&&(e+h)>f&&(e+h)<c;if(this.options.tolerance=="pointer"||this.options.forcePointerForContainers||(this.options.tolerance!="pointer"&&this.helperProportions[this.floating?"width":"height"]>m[this.floating?"width":"height"])){return g;
}else{return(f<e+(this.helperProportions.width/2)&&d-(this.helperProportions.width/2)<c&&n<k+(this.helperProportions.height/2)&&j-(this.helperProportions.height/2)<i);
}},_intersectsWithPointer:function(e){var f=(this.options.axis==="x")||a.ui.isOverAxis(this.positionAbs.top+this.offset.click.top,e.top,e.height),d=(this.options.axis==="y")||a.ui.isOverAxis(this.positionAbs.left+this.offset.click.left,e.left,e.width),h=f&&d,c=this._getDragVerticalDirection(),g=this._getDragHorizontalDirection();
if(!h){return false;}return this.floating?(((g&&g=="right")||c=="down")?2:1):(c&&(c=="down"?2:1));
},_intersectsWithSides:function(f){var d=a.ui.isOverAxis(this.positionAbs.top+this.offset.click.top,f.top+(f.height/2),f.height),e=a.ui.isOverAxis(this.positionAbs.left+this.offset.click.left,f.left+(f.width/2),f.width),c=this._getDragVerticalDirection(),g=this._getDragHorizontalDirection();
if(this.floating&&g){return((g=="right"&&e)||(g=="left"&&!e));}else{return c&&((c=="down"&&d)||(c=="up"&&!d));
}},_getDragVerticalDirection:function(){var c=this.positionAbs.top-this.lastPositionAbs.top;
return c!=0&&(c>0?"down":"up");},_getDragHorizontalDirection:function(){var c=this.positionAbs.left-this.lastPositionAbs.left;
return c!=0&&(c>0?"right":"left");},refresh:function(c){this._refreshItems(c);this.refreshPositions();
return this;},_connectWith:function(){var c=this.options;return c.connectWith.constructor==String?[c.connectWith]:c.connectWith;
},_getItemsAsjQuery:function(c){var m=this;var h=[];var f=[];var k=this._connectWith();
if(k&&c){for(var e=k.length-1;e>=0;e--){var l=a(k[e]);for(var d=l.length-1;d>=0;d--){var g=a.data(l[d],this.widgetName);
if(g&&g!=this&&!g.options.disabled){f.push([a.isFunction(g.options.items)?g.options.items.call(g.element):a(g.options.items,g.element).not(".ui-sortable-helper").not(".ui-sortable-placeholder"),g]);
}}}}f.push([a.isFunction(this.options.items)?this.options.items.call(this.element,null,{options:this.options,item:this.currentItem}):a(this.options.items,this.element).not(".ui-sortable-helper").not(".ui-sortable-placeholder"),this]);
for(var e=f.length-1;e>=0;e--){f[e][0].each(function(){h.push(this);});}return a(h);
},_removeCurrentsFromItems:function(){var e=this.currentItem.find(":data("+this.widgetName+"-item)");
for(var d=0;d<this.items.length;d++){for(var c=0;c<e.length;c++){if(e[c]==this.items[d].item[0]){this.items.splice(d,1);
}}}},_refreshItems:function(c){this.items=[];this.containers=[this];var k=this.items;
var q=this;var g=[[a.isFunction(this.options.items)?this.options.items.call(this.element[0],c,{item:this.currentItem}):a(this.options.items,this.element),this]];
var m=this._connectWith();if(m&&this.ready){for(var f=m.length-1;f>=0;f--){var n=a(m[f]);
for(var e=n.length-1;e>=0;e--){var h=a.data(n[e],this.widgetName);if(h&&h!=this&&!h.options.disabled){g.push([a.isFunction(h.options.items)?h.options.items.call(h.element[0],c,{item:this.currentItem}):a(h.options.items,h.element),h]);
this.containers.push(h);}}}}for(var f=g.length-1;f>=0;f--){var l=g[f][1];var d=g[f][0];
for(var e=0,o=d.length;e<o;e++){var p=a(d[e]);p.data(this.widgetName+"-item",l);k.push({item:p,instance:l,width:0,height:0,left:0,top:0});
}}},refreshPositions:function(c){if(this.offsetParent&&this.helper){this.offset.parent=this._getParentOffset();
}for(var e=this.items.length-1;e>=0;e--){var f=this.items[e];if(f.instance!=this.currentContainer&&this.currentContainer&&f.item[0]!=this.currentItem[0]){continue;
}var d=this.options.toleranceElement?a(this.options.toleranceElement,f.item):f.item;
if(!c){f.width=d.outerWidth();f.height=d.outerHeight();}var g=d.offset();f.left=g.left;
f.top=g.top;}if(this.options.custom&&this.options.custom.refreshContainers){this.options.custom.refreshContainers.call(this);
}else{for(var e=this.containers.length-1;e>=0;e--){var g=this.containers[e].element.offset();
this.containers[e].containerCache.left=g.left;this.containers[e].containerCache.top=g.top;
this.containers[e].containerCache.width=this.containers[e].element.outerWidth();this.containers[e].containerCache.height=this.containers[e].element.outerHeight();
}}return this;},_createPlaceholder:function(e){var c=e||this,f=c.options;if(!f.placeholder||f.placeholder.constructor==String){var d=f.placeholder;
f.placeholder={element:function(){var g=a(document.createElement(c.currentItem[0].nodeName)).addClass(d||c.currentItem[0].className+" ui-sortable-placeholder").removeClass("ui-sortable-helper")[0];
if(!d){g.style.visibility="hidden";}return g;},update:function(g,h){if(d&&!f.forcePlaceholderSize){return;
}if(!h.height()){h.height(c.currentItem.innerHeight()-parseInt(c.currentItem.css("paddingTop")||0,10)-parseInt(c.currentItem.css("paddingBottom")||0,10));
}if(!h.width()){h.width(c.currentItem.innerWidth()-parseInt(c.currentItem.css("paddingLeft")||0,10)-parseInt(c.currentItem.css("paddingRight")||0,10));
}}};}c.placeholder=a(f.placeholder.element.call(c.element,c.currentItem));c.currentItem.after(c.placeholder);
f.placeholder.update(c,c.placeholder);},_contactContainers:function(c){var e=null,l=null;
for(var g=this.containers.length-1;g>=0;g--){if(a.ui.contains(this.currentItem[0],this.containers[g].element[0])){continue;
}if(this._intersectsWith(this.containers[g].containerCache)){if(e&&a.ui.contains(this.containers[g].element[0],e.element[0])){continue;
}e=this.containers[g];l=g;}else{if(this.containers[g].containerCache.over){this.containers[g]._trigger("out",c,this._uiHash(this));
this.containers[g].containerCache.over=0;}}}if(!e){return;}if(this.containers.length===1){this.containers[l]._trigger("over",c,this._uiHash(this));
this.containers[l].containerCache.over=1;}else{if(this.currentContainer!=this.containers[l]){var k=10000;
var h=null;var d=this.positionAbs[this.containers[l].floating?"left":"top"];for(var f=this.items.length-1;
f>=0;f--){if(!a.ui.contains(this.containers[l].element[0],this.items[f].item[0])){continue;
}var m=this.containers[l].floating?this.items[f].item.offset().left:this.items[f].item.offset().top;
if(Math.abs(m-d)<k){k=Math.abs(m-d);h=this.items[f];this.direction=(m-d>0)?"down":"up";
}}if(!h&&!this.options.dropOnEmpty){return;}this.currentContainer=this.containers[l];
h?this._rearrange(c,h,null,true):this._rearrange(c,null,this.containers[l].element,true);
this._trigger("change",c,this._uiHash());this.containers[l]._trigger("change",c,this._uiHash(this));
this.options.placeholder.update(this.currentContainer,this.placeholder);this.containers[l]._trigger("over",c,this._uiHash(this));
this.containers[l].containerCache.over=1;}}},_createHelper:function(d){var e=this.options;
var c=a.isFunction(e.helper)?a(e.helper.apply(this.element[0],[d,this.currentItem])):(e.helper=="clone"?this.currentItem.clone():this.currentItem);
if(!c.parents("body").length){a(e.appendTo!="parent"?e.appendTo:this.currentItem[0].parentNode)[0].appendChild(c[0]);
}if(c[0]==this.currentItem[0]){this._storedCSS={width:this.currentItem[0].style.width,height:this.currentItem[0].style.height,position:this.currentItem.css("position"),top:this.currentItem.css("top"),left:this.currentItem.css("left")};
}if(c[0].style.width==""||e.forceHelperSize){c.width(this.currentItem.width());}if(c[0].style.height==""||e.forceHelperSize){c.height(this.currentItem.height());
}return c;},_adjustOffsetFromHelper:function(c){if(typeof c=="string"){c=c.split(" ");
}if(a.isArray(c)){c={left:+c[0],top:+c[1]||0};}if("left" in c){this.offset.click.left=c.left+this.margins.left;
}if("right" in c){this.offset.click.left=this.helperProportions.width-c.right+this.margins.left;
}if("top" in c){this.offset.click.top=c.top+this.margins.top;}if("bottom" in c){this.offset.click.top=this.helperProportions.height-c.bottom+this.margins.top;
}},_getParentOffset:function(){this.offsetParent=this.helper.offsetParent();var c=this.offsetParent.offset();
if(this.cssPosition=="absolute"&&this.scrollParent[0]!=document&&a.ui.contains(this.scrollParent[0],this.offsetParent[0])){c.left+=this.scrollParent.scrollLeft();
c.top+=this.scrollParent.scrollTop();}if((this.offsetParent[0]==document.body)||(this.offsetParent[0].tagName&&this.offsetParent[0].tagName.toLowerCase()=="html"&&a.browser.msie)){c={top:0,left:0};
}return{top:c.top+(parseInt(this.offsetParent.css("borderTopWidth"),10)||0),left:c.left+(parseInt(this.offsetParent.css("borderLeftWidth"),10)||0)};
},_getRelativeOffset:function(){if(this.cssPosition=="relative"){var c=this.currentItem.position();
return{top:c.top-(parseInt(this.helper.css("top"),10)||0)+this.scrollParent.scrollTop(),left:c.left-(parseInt(this.helper.css("left"),10)||0)+this.scrollParent.scrollLeft()};
}else{return{top:0,left:0};}},_cacheMargins:function(){this.margins={left:(parseInt(this.currentItem.css("marginLeft"),10)||0),top:(parseInt(this.currentItem.css("marginTop"),10)||0)};
},_cacheHelperProportions:function(){this.helperProportions={width:this.helper.outerWidth(),height:this.helper.outerHeight()};
},_setContainment:function(){var f=this.options;if(f.containment=="parent"){f.containment=this.helper[0].parentNode;
}if(f.containment=="document"||f.containment=="window"){this.containment=[0-this.offset.relative.left-this.offset.parent.left,0-this.offset.relative.top-this.offset.parent.top,a(f.containment=="document"?document:window).width()-this.helperProportions.width-this.margins.left,(a(f.containment=="document"?document:window).height()||document.body.parentNode.scrollHeight)-this.helperProportions.height-this.margins.top];
}if(!(/^(document|window|parent)$/).test(f.containment)){var d=a(f.containment)[0];
var e=a(f.containment).offset();var c=(a(d).css("overflow")!="hidden");this.containment=[e.left+(parseInt(a(d).css("borderLeftWidth"),10)||0)+(parseInt(a(d).css("paddingLeft"),10)||0)-this.margins.left,e.top+(parseInt(a(d).css("borderTopWidth"),10)||0)+(parseInt(a(d).css("paddingTop"),10)||0)-this.margins.top,e.left+(c?Math.max(d.scrollWidth,d.offsetWidth):d.offsetWidth)-(parseInt(a(d).css("borderLeftWidth"),10)||0)-(parseInt(a(d).css("paddingRight"),10)||0)-this.helperProportions.width-this.margins.left,e.top+(c?Math.max(d.scrollHeight,d.offsetHeight):d.offsetHeight)-(parseInt(a(d).css("borderTopWidth"),10)||0)-(parseInt(a(d).css("paddingBottom"),10)||0)-this.helperProportions.height-this.margins.top];
}},_convertPositionTo:function(g,i){if(!i){i=this.position;}var e=g=="absolute"?1:-1;
var f=this.options,c=this.cssPosition=="absolute"&&!(this.scrollParent[0]!=document&&a.ui.contains(this.scrollParent[0],this.offsetParent[0]))?this.offsetParent:this.scrollParent,h=(/(html|body)/i).test(c[0].tagName);
return{top:(i.top+this.offset.relative.top*e+this.offset.parent.top*e-(a.browser.safari&&this.cssPosition=="fixed"?0:(this.cssPosition=="fixed"?-this.scrollParent.scrollTop():(h?0:c.scrollTop()))*e)),left:(i.left+this.offset.relative.left*e+this.offset.parent.left*e-(a.browser.safari&&this.cssPosition=="fixed"?0:(this.cssPosition=="fixed"?-this.scrollParent.scrollLeft():h?0:c.scrollLeft())*e))};
},_generatePosition:function(f){var i=this.options,c=this.cssPosition=="absolute"&&!(this.scrollParent[0]!=document&&a.ui.contains(this.scrollParent[0],this.offsetParent[0]))?this.offsetParent:this.scrollParent,j=(/(html|body)/i).test(c[0].tagName);
if(this.cssPosition=="relative"&&!(this.scrollParent[0]!=document&&this.scrollParent[0]!=this.offsetParent[0])){this.offset.relative=this._getRelativeOffset();
}var e=f.pageX;var d=f.pageY;if(this.originalPosition){if(this.containment){if(f.pageX-this.offset.click.left<this.containment[0]){e=this.containment[0]+this.offset.click.left;
}if(f.pageY-this.offset.click.top<this.containment[1]){d=this.containment[1]+this.offset.click.top;
}if(f.pageX-this.offset.click.left>this.containment[2]){e=this.containment[2]+this.offset.click.left;
}if(f.pageY-this.offset.click.top>this.containment[3]){d=this.containment[3]+this.offset.click.top;
}}if(i.grid){var h=this.originalPageY+Math.round((d-this.originalPageY)/i.grid[1])*i.grid[1];
d=this.containment?(!(h-this.offset.click.top<this.containment[1]||h-this.offset.click.top>this.containment[3])?h:(!(h-this.offset.click.top<this.containment[1])?h-i.grid[1]:h+i.grid[1])):h;
var g=this.originalPageX+Math.round((e-this.originalPageX)/i.grid[0])*i.grid[0];e=this.containment?(!(g-this.offset.click.left<this.containment[0]||g-this.offset.click.left>this.containment[2])?g:(!(g-this.offset.click.left<this.containment[0])?g-i.grid[0]:g+i.grid[0])):g;
}}return{top:(d-this.offset.click.top-this.offset.relative.top-this.offset.parent.top+(a.browser.safari&&this.cssPosition=="fixed"?0:(this.cssPosition=="fixed"?-this.scrollParent.scrollTop():(j?0:c.scrollTop())))),left:(e-this.offset.click.left-this.offset.relative.left-this.offset.parent.left+(a.browser.safari&&this.cssPosition=="fixed"?0:(this.cssPosition=="fixed"?-this.scrollParent.scrollLeft():j?0:c.scrollLeft())))};
},_rearrange:function(h,g,d,f){d?d[0].appendChild(this.placeholder[0]):g.item[0].parentNode.insertBefore(this.placeholder[0],(this.direction=="down"?g.item[0]:g.item[0].nextSibling));
this.counter=this.counter?++this.counter:1;var e=this,c=this.counter;window.setTimeout(function(){if(c==e.counter){e.refreshPositions(!f);
}},0);},_clear:function(e,f){this.reverting=false;var g=[],c=this;if(!this._noFinalSort&&this.currentItem.parent().length){this.placeholder.before(this.currentItem);
}this._noFinalSort=null;if(this.helper[0]==this.currentItem[0]){for(var d in this._storedCSS){if(this._storedCSS[d]=="auto"||this._storedCSS[d]=="static"){this._storedCSS[d]="";
}}this.currentItem.css(this._storedCSS).removeClass("ui-sortable-helper");}else{this.currentItem.show();
}if(this.fromOutside&&!f){g.push(function(h){this._trigger("receive",h,this._uiHash(this.fromOutside));
});}if((this.fromOutside||this.domPosition.prev!=this.currentItem.prev().not(".ui-sortable-helper")[0]||this.domPosition.parent!=this.currentItem.parent()[0])&&!f){g.push(function(h){this._trigger("update",h,this._uiHash());
});}if(this!==this.currentContainer){if(!f){g.push(function(h){this._trigger("remove",h,this._uiHash());
});g.push((function(h){return function(i){h._trigger("receive",i,this._uiHash(this));
};}).call(this,this.currentContainer));g.push((function(h){return function(i){h._trigger("update",i,this._uiHash(this));
};}).call(this,this.currentContainer));}}for(var d=this.containers.length-1;d>=0;
d--){if(!f){g.push((function(h){return function(i){h._trigger("deactivate",i,this._uiHash(this));
};}).call(this,this.containers[d]));}if(this.containers[d].containerCache.over){g.push((function(h){return function(i){h._trigger("out",i,this._uiHash(this));
};}).call(this,this.containers[d]));this.containers[d].containerCache.over=0;}}if(this._storedCursor){a("body").css("cursor",this._storedCursor);
}if(this._storedOpacity){this.helper.css("opacity",this._storedOpacity);}if(this._storedZIndex){this.helper.css("zIndex",this._storedZIndex=="auto"?"":this._storedZIndex);
}this.dragging=false;if(this.cancelHelperRemoval){if(!f){this._trigger("beforeStop",e,this._uiHash());
for(var d=0;d<g.length;d++){g[d].call(this,e);}this._trigger("stop",e,this._uiHash());
}this.fromOutside=false;return false;}if(!f){this._trigger("beforeStop",e,this._uiHash());
}this.placeholder[0].parentNode.removeChild(this.placeholder[0]);if(this.helper[0]!=this.currentItem[0]){this.helper.remove();
}this.helper=null;if(!f){for(var d=0;d<g.length;d++){g[d].call(this,e);}this._trigger("stop",e,this._uiHash());
}this.fromOutside=false;return true;},_trigger:function(){if(a.Widget.prototype._trigger.apply(this,arguments)===false){this.cancel();
}},_uiHash:function(d){var c=d||this;return{helper:c.helper,placeholder:c.placeholder||a([]),position:c.position,originalPosition:c.originalPosition,offset:c.positionAbs,item:c.currentItem,sender:d?d.element:null};
}});a.extend(a.ui.sortable,{version:"1.8.24"});})(jQuery);