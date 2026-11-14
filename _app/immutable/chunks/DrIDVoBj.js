const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./w3L-
XTi5.js","./CGAj-1JJ.js","./B1INsJo1.js","./hAjDEfIC.js","./CnHNO-
C3.js","./BWNLh2yq.js","./DAx5FZmr.js","./D6oohdKz.js","./CCZvg3YS.js","./CpZ_Wj
y7.js"])))=>i.map(i=>d[i]); import{t as e}from"./DclECHGd.js";var t={},n=[`ru`,`
en`,`es`,`pt`,`uz`,`fr`,`be`,`nn`],r=`PARAGLIDE_LOCALE`,i=[`custom-oneme-
strategy`,`baseLocale`],a=[],o,s;function c(e){if(a.length===0)return;let 
n=typeof e==`string`?e:e.href;if(o===n)return s;let r=new 
URL(n,`http://dummy.com`),i;for(let e of a)if(new 
t(e.match,r.href).exec(r.href)){i=e;break}return o=n,s=i,i}function l(e){let 
t=c(e);return t&&t.exclude!==!0&&Array.isArray(t.strategy)?t.strategy:i}globalTh
is.__paraglide=globalThis.__paraglide??{},globalThis.__paraglide.ssr=globalThis.
__paraglide.ssr??{};var u=!1,d=()=>{let e=i;typeof 
window<`u`&&window.location?.href&&(e=l(window.location.href));let 
t=f(e,typeof window<`u`?window.location?.href:void 0);if(t)return 
u||(u=!0,m(t,{reload:!1})),t;throw Error(`No locale found. Read the docs 
https://paraglidejs.com/errors#no-locale-found`)};function f(e,t){let n;for(let 
t of e){if(t===`baseLocale`)n=`ru`;else if(b(t)&&y.has(t)){let 
e=y.get(t);if(e){let t=e.getLocale();if(t instanceof 
Promise)continue;if(t!==void 0)return g(t)}}let e=h(n);if(e)return e}}var 
p=e=>{e?window.location.href=e:window.location.reload()},m=(e,t)=>{let 
n={reload:!0,...t},r;try{r=d()}catch{}let a=[],o=i;typeof 
window<`u`&&window.location?.href&&(o=l(window.location.href));for(let t of 
o)if(t===`baseLocale`)continue;else if(b(t)&&y.has(t)){let n=y.get(t);if(n){let 
r=n.setLocale(e);r instanceof Promise&&(r=r.catch(e=>{throw Error(`Custom 
strategy "${t}" setLocale failed.`,{cause:e})}),a.push(r))}}let 
s=()=>{n.reload&&window.location&&e!==r&&p(void 0)};if(a.length)return 
Promise.all(a).then(()=>{s()});s()};function h(e){if(typeof 
e!=`string`)return;let t=e.toLowerCase();for(let e of 
n)if(e.toLowerCase()===t)return e}function g(e){let t=h(e);if(t)return t;throw 
Error(`Invalid locale: ${e}. Expected one of: ${n.join(`, `)}`)}var _=r.replace(
/[.*+?^${}()|[\]\\]/g,`\\$&`);RegExp(`(?:^|;\\s*)${_}=([^;]*)`);function 
v(){if(!navigator?.languages?.length)return;let