import{$ as e,$t as t,A as n,E as r,Et as i,Ht as a,J as o,Jt as s,N as c,Pt as 
l,Q as u,Qt as d,Tt as f,U as p,Vt as m,W as h,X as g,at as _,dt as v,et as y,h 
as b,it as x,j as S,jt as C,k as w,kt as T,m as ee,o as E,q as D,qt as te,r as 
O,rt as k,tt as A,u as ne,wt as j,yt as M}from"./C5uw_Ui6.js";import{Al as re,Bl
 as ie,Bs as N,Bt as P,Fl as ae,Gs as F,It as I,Lt as L,Ol as oe,Pl as se,Ql as 
R,Vs as z,Ys as B,Zs as V,al as H,mn as U,qt as W,si as G,un as ce,vn as K,yn as
 q}from"./Cf8hdRU_.js";import"./xihTtKlq.js";import{s as 
le}from"./Cu_Pov8T.js";le(``,`icon_gif_fill_mini`);var ue=A(``);function 
de(e,t){a(t,!0);var 
n=ue();M(()=>{r(n,`width`,t.size),r(n,`height`,t.size),w(n,t.color?`color: 
var(--icon-${t.color}, currentColor)`:``)}),u(e,n),m()}var 
fe=A(``),pe=A(``,1),me=A(``,1),he=y(``);function J(e,t){let n=l(()=>Math.round(t
.size/10)),a=l(()=>(t.size-v(n))/2.3),o=l(()=>2*Math.PI*v(a)),c=l(()=>v(o)*(1-
t.progress)),d=l(()=>t.size/2/20),p=l(()=>(t.size-20)/2);var 
m=he(),h=j(m),g=j(h),y=i(g),b=e=>{var t=fe();M(()=>w(t,`transform: 
scale(${v(d)??``}) translate(${v(p)??``}px, ${v(p)??``}px)`)),u(e,t)},x=e=>{var 
s=me(),l=f(s),d=i(l),p=e=>{var n=pe(),a=f(n),o=i(a);M(()=>{r(a,`x1`,t.size/2-
7),r(a,`y1`,t.size/2-
7),r(a,`x2`,t.size/2+7),r(a,`y2`,t.size/2+7),r(o,`x1`,t.size/2-
7),r(o,`y1`,t.size/2+7),r(o,`x2`,t.size/2+7),r(o,`y2`,t.size/2-
7)}),u(e,n)};D(d,e=>{t.onAbort&&e(p)}),M(()=>{r(l,`cx`,t.size/2),r(l,`cy`,t.size
/2),r(l,`stroke-width`,v(n)),r(l,`r`,v(a)),r(l,`stroke-
dasharray`,v(o)),r(l,`stroke-dashoffset`,v(c))}),u(e,s)};D(y,e=>{t.onRetry?e(b):
e(x,-1)}),s(h),s(m),M(()=>{r(m,`aria-label`,t.onRetry?`Повторить 
загрузку`:`Отменить загрузку`),r(h,`data-
c`,v(o)),r(h,`width`,t.size),r(h,`height`,t.size),r(h,`viewBox`,`0 0 
${t.size??``} ${t.size??``}`),r(g,`cx`,t.size/2),r(g,`cy`,t.size/2),r(g,`r`,t.si