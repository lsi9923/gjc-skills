var content=(function() {
  "use strict";
  function tt(t) {
    return t
  }
  const V= {
    matches:["*://search.shopping.naver.com/search/*","*://www.coupang.com/np/search*"],runAt:"document_end",allFrames:!0,main() {
      const t="nvs-word-cloud-container",o=["10대","20대","30대","40대","50대","60대","70대","무료","오늘","배송","쿠팡","로켓"];
      function i(r) {
        const s=r.trim(),a=o.some(p=>s.includes(p));
        return s&&s.length>1&&!a?s:null
      }
      function l() {
        try {
          const r=document.querySelector("#__NEXT_DATA__");
          if(!r)return[];
          const s=r.textContent||"",p=JSON.parse(s)?.props?.pageProps?.compositeList?.list||[],n=new Set;
          return p.forEach(e=> {
            const b=(e.item||e).manuTag||"";
            b&&String(b).split(",").forEach(y=> {
              const I=i(y);
              I&&n.add(I)
            }
            )
          }
          ),Array.from(n).sort()
        }
        catch {
          return[]
        }
      }
      function v() {
        try {
          const r=new Set;
          return document.querySelectorAll(".autocomplete_wrap a, .autocomplete_wrap li").forEach(a=> {
            const p=a.getAttribute("data-searchkeyword")||a.getAttribute("data-keyword");
            if(p)r.add(p.trim());
            else {
              const n=a.textContent?.trim();
              n&&r.add(n)
            }
          }
          ),Array.from(r).filter(a=>a.length>1)
        }
        catch {
          return[]
        }
      }
      function X() {
        let r=null;
        const s=async()=> {
          const n=v();
          if(n.length>0) {
            S=n;
            const e=await H();
            E(n,!0,z(),e.count)
          }
        }
        ,a=()=> {
          r&&clearTimeout(r),r=setTimeout(s,200)
        }
        ;
        document.addEventListener("focusin",n=> {
          n.target.matches?.("#headerSearchKeyword, .search-input")&&(a(),setTimeout(a,500))
        }
        ),document.addEventListener("input",n=> {
          n.target.matches?.("#headerSearchKeyword, .search-input")&&a()
        }
        ),new MutationObserver(n=> {
          let e=!1;
          for(const d of n)if(d.type==="childList"&&Array.from(d.addedNodes).some(y=>y instanceof HTMLElement&&(y.classList.contains("autocomplete_wrap")||y.querySelector(".autocomplete_wrap")))) {
            e=!0;
            break
          }
          (e||document.querySelector(".autocomplete_wrap"))&&a()
        }
        ).observe(document.body, {
          childList:!0,subtree:!0
        }
        ),s()
      }
      function z() {
        const r=new URL(window.location.href);
        return r.searchParams.get("q")||r.searchParams.get("query")||""
      }
      let S=[],P="",R=!1,D="";
      const q=20;
      async function H() {
        return new Promise(r=> {
          const s=new Date().toISOString().split("T")[0],a="daily_usage",n=window.chrome?.storage?.local;
          if(!n) {
            console.warn("Storage API not available"),r( {
              allowed:!0,count:0
            }
            );
            return
          }
          n.get([a],e=> {
            let d=e[a]|| {
              date:s,count:0
            }
            ;
            if(d.date!==s&&(d= {
              date:s,count:0
            }
            ),d.count>=q) {
              r( {
                allowed:!1,count:d.count
              }
              );
              return
            }
            const b=z();
            b&&b!==D?(d.count++,D=b,n.set( {
              [a]:d
            }
            ),r( {
              allowed:!0,count:d.count
            }
            )):r( {
              allowed:!0,count:d.count
            }
            )
          }
          )
        }
        )
      }
      async function M() {
        if(!window.location.href.includes("/search"))return;
        const s=window.location.hostname.includes("coupang.com"),a=z(),p=s?"#0074e9":"#03c75a";
        let n=document.getElementById(t);
        n||(n=document.createElement("div"),n.id=t,n.style.cssText=`
					padding: 20px;
         margin: 20px auto;
         background: #fff;
        
					border-top: 4px solid $ {
          p
        }
        ;
         border-radius: 12px;
        
					border-left: 1px solid #eee;
         border-right: 1px solid #eee;
         border-bottom: 1px solid #eee;
        
					z-index: 100;
         position: relative;
         width: 100%;
         box-sizing: border-box;
        
					box-shadow: none;
         font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        
				`,(document.querySelector('[class*="srp_resultHeader"]')||document.querySelector("#content")||document.querySelector('[class*="search_list_area"]')||document.querySelector("#productList")||document.body).prepend(n));
        const e=await H();
        if(n.innerHTML.trim()===""&&(n.innerHTML=`
					<div style="padding: 20px; text-align: center; color: #888;">
						<div style="font-size: 14px;">데이터를 불러오는 중입니다...</div>
					</div>
				`),!e.allowed) {
          n.innerHTML=`
					<div style="padding: 20px; text-align: center; color: #333;">
						<div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">일일 조회수를 초과했습니다.</div>
						<div style="font-size: 13px; color: #666; margin-bottom: 12px;">추가 사용을 원하시면 메이커에게 요청해 주세요.</div>
						<div style="font-size: 12px; color: #999; background: #f5f5f5; display: inline-block; padding: 4px 10px; border-radius: 12px; margin-bottom: 16px;">
							오늘 사용량: <span style="color: ${p}; font-weight: bold;">$ {
            e.count
          }
          </span> / $ {
            q
          }
          
						</div>
						<div style="margin-top: 16px;">
								<a href="https://www.youtube.com/channel/UCJNNgWjaZdMRquZKAp3EKuw" target="_blank" style="display: inline-block; background: #f8f9fa; color: #495057; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; border: 1px solid #dee2e6; transition: all 0.2s ease;">
									📺 메이커 유튜브 방문하기
								</a>
							</div>
					</div>
				`;
          return
        }
        if(s&&a===P&&S.length>0) {
          E(S,s,a,e.count);
          return
        }
        if(s)R||(X(),R=!0),P=a,S.length>0?E(S,s,a,e.count):E([],s,a,e.count);
        else {
          const d=l();
          E(d,s,a,e.count)
        }
      }
      function E(r,s,a,p=0) {
        const n=document.getElementById(t);
        if(!n)return;
        const e=s?"#0074e9":"#03c75a",d=s?"쿠팡 자동완성 키워드":"네이버쇼핑 태그",b="https://www.youtube.com/channel/UCJNNgWjaZdMRquZKAp3EKuw",y=`
				<svg viewBox="0 0 24 24" width="16" height="16" style="fill: #666; vertical-align: middle; margin-right: 4px;">
					<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"></circle>
					<path d="M10 8l6 4-6 4V8z" fill="currentColor"></path>
				</svg>
			`,I=`
				background: #f8f9fa;
        
				color: #333;
        
				padding: 6px 12px;
        
				border-radius: 8px;
        
				border: 1px solid #eee;
        
				font-size: 13px;
        
				font-weight: 500;
        
				cursor: pointer;
        
				transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        
				display: inline-flex;
        
				align-items: center;
        
				box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        
				user-select: none;
        
			`;
        if(!document.getElementById(`$ {
          t
        }
        -styles`)) {
          const c=document.createElement("style");
          c.id=`$ {
            t
          }
          -styles`,c.textContent=`
					.nvs-chip:hover  {
            
						background: #fff !important;
            
						border-color: $ {
              e
            }
             !important;
            
						color: $ {
              e
            }
             !important;
            
						transform: translateY(-2px);
            
						box-shadow: 0 4px 12px $ {
              e
            }
            15 !important;
          }
          
					.nvs-chip.selected  {
            
						background: $ {
              e
            }
             !important;
            
						color: white !important;
            
						border-color: $ {
              e
            }
             !important;
            
						box-shadow: 0 4px 12px $ {
              e
            }
            40 !important;
          }
          
					.nvs-copy-btn:hover  {
            
						opacity: 0.9;
            
						transform: scale(1.02);
          }
          
					.nvs-copy-btn:active  {
            
						transform: scale(0.98);
          }
          
				`,document.head.appendChild(c)
        }
        const N=`
				<span style="font-size: 11px; color: #999; margin-right: 12px; background: #f5f5f5; padding: 2px 8px; border-radius: 10px;">
					오늘 사용량: <span style="color: ${e}; font-weight: bold;">$ {
          p
        }
        </span>/$ {
          q
        }
        
				</span>
			`,B='<div style="font-size: 11px; color: #ccc; font-weight: 500; text-align: right; margin-top: 12px;">메이커 셀링 도우미 v0.0.3</div>';
        if(s&&r.length===0) {
          n.innerHTML=`
					<div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
						<span style="font-weight: 700; font-size: 15px; color: #111;">$ {
            d
          }
           <span style="color: #999; font-weight: 400; font-size: 13px;">(대기 중)</span></span>
						<div style="display: flex; align-items: center;">
							$ {
            N
          }
          
							<a href="${b}" target="_blank" style="color: #666; font-size: 12px; text-decoration: none; display: flex; align-items: center; background: #f0f0f0; padding: 4px 10px; border-radius: 20px;">
								$ {
            y
          }
           메이커 유튜브 방문하기
							</a>
						</div>
					</div>
					<div style="color: #888; font-size: 14px; background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px dashed #ddd; text-align: center;">
						상단 검색창을 클릭하거나 검색어를 입력하면 키워드가 여기에 표시됩니다.
					</div>
					$ {
            B
          }
          
				`;
          return
        }
        if(!s&&r.length===0) {
          n.innerHTML=`
					<div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
						<div style="display: flex; align-items: center; gap: 10px;">
							<span style="font-weight: 700; font-size: 15px; color: #111;">$ {
            d
          }
          </span>
							<button id="${t}-retry-btn" style="background: #f0f0f0; color: #666; border: none; padding: 4px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; font-weight: 500;">재시도</button>
						</div>
						<div style="display: flex; align-items: center;">
							$ {
            N
          }
          
							<a href="${b}" target="_blank" style="color: #666; font-size: 12px; text-decoration: none; display: flex; align-items: center; background: #f0f0f0; padding: 4px 10px; border-radius: 20px;">
								$ {
            y
          }
           메이커 유튜브 방문하기
							</a>
						</div>
					</div>
					<div style="color: #888; font-size: 14px; background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px dashed #ddd; text-align: center;">
						태그를 찾는 중입니다...
					</div>
					$ {
            B
          }
          
				`;
          const c=document.getElementById(`$ {
            t
          }
          -retry-btn`);
          c&&(c.onclick=()=>M());
          return
        }
        n.innerHTML=`
				<div style="font-weight: bold; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
					<div style="display: flex; align-items: center; gap: 8px;">
						<span style="font-size: 17px; font-weight: 800; color: #111; letter-spacing: -0.5px;">$ {
          d
        }
         <span style="color: ${e}; font-size: 14px; margin-left: 4px;">$ {
          r.length
        }
        개</span></span>
						<div style="display: flex; gap: 6px; margin-left: 8px;">
							<button id="${t}-random-10-btn" class="nvs-copy-btn" style="background: #f8f9fa; color: #555; border: 1px solid #ddd; padding: 6px 10px; border-radius: 8px; font-size: 11px; cursor: pointer; font-weight: 500;">
								10개 랜덤
							</button>
							<button id="${t}-random-20-btn" class="nvs-copy-btn" style="background: #f8f9fa; color: #555; border: 1px solid #ddd; padding: 6px 10px; border-radius: 8px; font-size: 11px; cursor: pointer; font-weight: 500;">
								20개 랜덤
							</button>
							<button id="${t}-reset-btn" class="nvs-copy-btn" style="background: #fff; color: #666; border: 1px solid #ddd; padding: 6px 10px; border-radius: 8px; font-size: 11px; cursor: pointer; font-weight: 500; display: none;">
								선택 초기화
							</button>
							<button id="${t}-select-copy-btn" class="nvs-copy-btn" style="background: #fff; color: ${e}; border: 1px solid ${e}; padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; font-weight: 600; transition: all 0.2s; display: none;">
								선택 복사
							</button>
							<button id="${t}-copy-btn" class="nvs-copy-btn" style="background: ${e}; color: white; border: none; padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 12px ${e}30;">
								전체 복사
							</button>
						</div>
					</div>
					<div style="display: flex; align-items: center;">
						$ {
          N
        }
        
						<a href="${b}" target="_blank" style="color: #666; font-size: 12px; text-decoration: none; display: flex; align-items: center; background: #f8f9fa; padding: 6px 12px; border-radius: 20px; border: 1px solid #eee;">
							$ {
          y
        }
         메이커 유튜브 방문하기
						</a>
					</div>
				</div>
				
				<div style="display: flex; flex-wrap: wrap; gap: 8px; padding: 4px;">
					$ {
          r.map(c=>`<span class="nvs-chip" style="${I}">$ {
            c
          }
          </span>`).join("")
        }
        
				</div>
				$ {
          B
        }
        
			`;
        const m=new Set,g=document.getElementById(`$ {
          t
        }
        -select-copy-btn`),w=document.getElementById(`$ {
          t
        }
        -reset-btn`),A=()=> {
          m.size>0?(g.style.display="inline-block",g.textContent=`$ {
            m.size
          }
          개 복사`,w&&(w.style.display="inline-block")):(g.style.display="none",w&&(w.style.display="none"))
        }
        ;
        w&&(w.onclick=()=> {
          m.clear(),A(),n.querySelectorAll(".nvs-chip").forEach(c=> {
            c.classList.remove("selected"),c.style.background="#f8f9fa",c.style.color="#333",c.style.borderColor="#eee"
          }
          )
        }
        ),g&&(g.onclick=()=> {
          const c=Array.from(m).join(", ");
          navigator.clipboard.writeText(c).then(()=> {
            g.textContent="복사 완료!",g.style.background="#333",g.style.color="#fff",g.style.borderColor="#333",setTimeout(()=> {
              A(),g.style.background="#fff",g.style.color=e,g.style.borderColor=e
            }
            ,1500)
          }
          )
        }
        );
        const h=document.getElementById(`$ {
          t
        }
        -copy-btn`);
        h&&(h.onclick=()=> {
          const c=r.join(", ");
          navigator.clipboard.writeText(c).then(()=> {
            const $=h.textContent;
            h.textContent="복사 완료!",h.style.background="#333",setTimeout(()=> {
              h.textContent=$,h.style.background=e
            }
            ,2e3)
          }
          )
        }
        );
        const W=c=> {
          const $=m.size,f=c-$;
          if(f<=0)return;
          const x=r.filter(u=>!m.has(u));
          for(let u=x.length-1;
          u>0;
          u--) {
            const L=Math.floor(Math.random()*(u+1));
            [x[u],x[L]]=[x[L],x[u]]
          }
          x.slice(0,f).forEach(u=> {
            m.add(u)
          }
          ),A(),n.querySelectorAll(".nvs-chip").forEach(u=> {
            const L=u.textContent||"";
            m.has(L)&&(u.classList.add("selected"),u.style.background=e,u.style.color="white",u.style.borderColor=e)
          }
          )
        }
        ,j=document.getElementById(`$ {
          t
        }
        -random-10-btn`);
        j&&(j.onclick=()=>W(10));
        const F=document.getElementById(`$ {
          t
        }
        -random-20-btn`);
        F&&(F.onclick=()=>W(20)),n.querySelectorAll(".nvs-chip").forEach(c=> {
          c.onclick=$=> {
            const f=$.currentTarget,x=f.textContent||"";
            f.classList.contains("selected")?(f.classList.remove("selected"),f.style.background="#f8f9fa",f.style.color="#333",f.style.borderColor="#eee",m.delete(x)):(f.classList.add("selected"),f.style.background=e,f.style.color="white",f.style.borderColor=e,m.add(x)),A()
          }
        }
        )
      }
      M();
      let K=window.location.href;
      new MutationObserver(()=> {
        const r=document.getElementById(t),s=document.querySelector('[class*="srp_resultHeader"]')||document.querySelector("#content")||document.querySelector('[class*="search_list_area"]')||document.querySelector("#productList");
        (window.location.href!==K||!r&&s)&&(K=window.location.href,M())
      }
      ).observe(document.body, {
        childList:!0,subtree:!0
      }
      )
    }
  }
  ;
  function T(t,...o) {
  }
  const Y= {
    debug:(...t)=>T(console.debug,...t),log:(...t)=>T(console.log,...t),warn:(...t)=>T(console.warn,...t),error:(...t)=>T(console.error,...t)
  }
  ,U=globalThis.browser?.runtime?.id?globalThis.browser:globalThis.chrome;
  var G=class O extends Event {
    static EVENT_NAME=_("wxt:locationchange");
    constructor(o,i) {
      super(O.EVENT_NAME, {
      }
      ),this.newUrl=o,this.oldUrl=i
    }
  }
  ;
  function _(t) {
    return`$ {
      U?.runtime?.id
    }
    :content:$ {
      t
    }
    `
  }
  function Q(t) {
    let o,i;
    return {
      run() {
        o==null&&(i=new URL(location.href),o=t.setInterval(()=> {
          let l=new URL(location.href);
          l.href!==i.href&&(window.dispatchEvent(new G(l,i)),i=l)
        }
        ,1e3))
      }
    }
  }
  var Z=class k {
    static SCRIPT_STARTED_MESSAGE_TYPE=_("wxt:content-script-started");
    id;
    abortController;
    locationWatcher=Q(this);
    constructor(o,i) {
      this.contentScriptName=o,this.options=i,this.id=Math.random().toString(36).slice(2),this.abortController=new AbortController,this.stopOldScripts(),this.listenForNewerScripts()
    }
    get signal() {
      return this.abortController.signal
    }
    abort(o) {
      return this.abortController.abort(o)
    }
    get isInvalid() {
      return U.runtime?.id==null&&this.notifyInvalidated(),this.signal.aborted
    }
    get isValid() {
      return!this.isInvalid
    }
    onInvalidated(o) {
      return this.signal.addEventListener("abort",o),()=>this.signal.removeEventListener("abort",o)
    }
    block() {
      return new Promise(()=> {
      }
      )
    }
    setInterval(o,i) {
      const l=setInterval(()=> {
        this.isValid&&o()
      }
      ,i);
      return this.onInvalidated(()=>clearInterval(l)),l
    }
    setTimeout(o,i) {
      const l=setTimeout(()=> {
        this.isValid&&o()
      }
      ,i);
      return this.onInvalidated(()=>clearTimeout(l)),l
    }
    requestAnimationFrame(o) {
      const i=requestAnimationFrame((...l)=> {
        this.isValid&&o(...l)
      }
      );
      return this.onInvalidated(()=>cancelAnimationFrame(i)),i
    }
    requestIdleCallback(o,i) {
      const l=requestIdleCallback((...v)=> {
        this.signal.aborted||o(...v)
      }
      ,i);
      return this.onInvalidated(()=>cancelIdleCallback(l)),l
    }
    addEventListener(o,i,l,v) {
      i==="wxt:locationchange"&&this.isValid&&this.locationWatcher.run(),o.addEventListener?.(i.startsWith("wxt:")?_(i):i,l, {
        ...v,signal:this.signal
      }
      )
    }
    notifyInvalidated() {
      this.abort("Content script context invalidated"),Y.debug(`Content script "${this.contentScriptName}" context invalidated`)
    }
    stopOldScripts() {
      document.dispatchEvent(new CustomEvent(k.SCRIPT_STARTED_MESSAGE_TYPE, {
        detail: {
          contentScriptName:this.contentScriptName,messageId:this.id
        }
      }
      )),window.postMessage( {
        type:k.SCRIPT_STARTED_MESSAGE_TYPE,contentScriptName:this.contentScriptName,messageId:this.id
      }
      ,"*")
    }
    verifyScriptStartedEvent(o) {
      const i=o.detail?.contentScriptName===this.contentScriptName,l=o.detail?.messageId===this.id;
      return i&&!l
    }
    listenForNewerScripts() {
      const o=i=> {
        !(i instanceof CustomEvent)||!this.verifyScriptStartedEvent(i)||this.notifyInvalidated()
      }
      ;
      document.addEventListener(k.SCRIPT_STARTED_MESSAGE_TYPE,o),this.onInvalidated(()=>document.removeEventListener(k.SCRIPT_STARTED_MESSAGE_TYPE,o))
    }
  }
  ;
  function nt() {
  }
  function C(t,...o) {
  }
  const J= {
    debug:(...t)=>C(console.debug,...t),log:(...t)=>C(console.log,...t),warn:(...t)=>C(console.warn,...t),error:(...t)=>C(console.error,...t)
  }
  ;
  return(async()=> {
    try {
      const {
        main:t,...o
      }
      =V;
      return await t(new Z("content",o))
    }
    catch(t) {
      throw J.error('The content script "content" crashed on startup!',t),t
    }
  }
  )()
}
)();

content;
