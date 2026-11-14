import{Et as e,Ht as t,N as n,T as r,Ut as i,Yt as a,at as o,it as s,nt as c,x 
as l,xt as u}from"./D45Wd9pD.js";function d(){if(typeof window>`u`||typeof 
document>`u`)return()=>()=>{};let 
e=window._SVG_SPRITE_IDS_=window._SVG_SPRITE_IDS_||new Set,t=document.createElem
entNS(`http://www.w3.org/2000/svg`,`svg`);t.style.position=`absolute`,t.style.wi
dth=`0`,t.style.height=`0`,t.style.overflow=`hidden`,t.ariaHidden=`true`,t.id=`m
ax-icons-sprite`;function 
n(){document.body.insertBefore(t,document.body.firstChild)}return document.ready
State===`loading`?document.addEventListener(`DOMContentLoaded`,n):n(),function(n
,r){(e.has(r)||document.getElementById(r))&&console.warn(`Icon #${r} was 
repeatedly registered. It must be globally 
unique.`),e.add(r),t.insertAdjacentHTML(`beforeend`,n);let i=t.lastChild;return 
function(){e.delete(r),i?.remove()}}}var f=d();f(``,`icon_spinner_android`);var 
p=o(``);function m(e,n){i(n,!0);var 
a=p();u(()=>{l(a,`width`,n.size),l(a,`height`,n.size),r(a,n.color?`color: 
var(--icon-${n.color}, currentColor)`:``)}),c(e,a),t()}var h=e=>e;function 
g(e){let t=e-1;return t*t*t+1}function _(e){return 
e<.5?4*e*e*e:.5*(2*e-2)**3+1}function v(e){let t=typeof 
e==`string`&&e.match(/^\s*(-?[\d.]+)([^\s]*)\s*$/);return 
t?[parseFloat(t[1]),t[2]||`px`]:[e,`px`]}function y(e,t,n){return 
Number.isNaN(t)?``:`${e}: ${n*t}px;`}function 
b(e,{delay:t=0,duration:n=400,easing:r=h}={}){let i=+getComputedStyle(e).opacity
;return{delay:t,duration:n,easing:r,css:e=>`opacity: ${e*i}`}}function 
x(e,{delay:t=0,duration:n=400,easing:r=g,x:i=0,y:a=0,opacity:o=0}={}){let s=getC
omputedStyle(e),c=+s.opacity,l=s.transform===`none`?``:s.transform,u=c*(1-
o),[d,f]=v(i),[p,m]=v(a);return{delay:t,duration:n,easing:r,css:(e,t)=>` 
transform: ${l} translate(${(1-e)*d}${f}, ${(1-e)*p}${m}); opacity: 
${c-u*t}`}}function S(e,{delay:t=0,duration:n=400,easing:r=g,axis:i=`y`}={}){let
 a=getComputedStyle(e),o=+a.opacity,s=i===`y`?`height`:`width`,c=parseFloat(a[s]
),l=i===`y`?[`top`,`bottom`]:[`left`,`right`],u=l.map(e=>`${e[0].toUpperCase()}$
{e.slice(1)}`),d=parseFloat(a[`padding${u[0]}`]),f=parseFloat(a[`padding${u[1]}`
]),p=parseFloat(a[`margin${u[0]}`]),m=parseFloat(a[`margin${u[1]}`]),h=parseFloa