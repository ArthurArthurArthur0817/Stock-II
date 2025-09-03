/* ========== Tutorial v5 (image slideshow) ========== */
(function(global){
  const LS_PREFIX = 'imgTutorialSeen';

  function keyOf(version, pageKey){
    return `${LS_PREFIX}:${version}:${pageKey}`;
  }

  function createEl(tag, cls, html){
    const el = document.createElement(tag);
    if(cls) el.className = cls;
    if(html != null) el.innerHTML = html;
    return el;
  }

  function initImageTutorial(opts){
    const {
      pageKey,
      version = 'img-v1',
      images = [],
      autoShow = false,
      enableEsc = true
    } = opts || {};

    if(!Array.isArray(images) || images.length === 0){
      console.warn('[tutorial] no images'); 
      return { show(){}, hide(){}, clear(){} };
    }

    const lsKey = keyOf(version, pageKey);
    const seen = localStorage.getItem(lsKey) === '1';

    // Build DOM
    const overlay = createEl('div', 'tut-overlay', '');
    overlay.setAttribute('role','dialog'); overlay.setAttribute('aria-modal','true');

    const frame = createEl('div', 'tut-frame');
    overlay.appendChild(frame);

    const slides = images.map((src, idx) => {
      const slide = createEl('div', 'tut-slide' + (idx===0?' is-active':'')); 
      const img = createEl('img', null);
      img.src = src;
      img.alt = `tutorial ${idx+1}/${images.length}`;
      slide.appendChild(img);
      frame.appendChild(slide);
      return slide;
    });

    // Controls
    const btnPrev  = createEl('button', 'tut-prev',  '');
    const btnNext  = createEl('button', 'tut-next',  '');
    const btnClose = createEl('button', 'tut-close', '×');
    const footer   = createEl('div', 'tut-footer');
    const btnDone  = createEl('button','tut-done','我知道了');

    frame.appendChild(btnPrev);
    frame.appendChild(btnNext);
    frame.appendChild(btnClose);
    frame.appendChild(footer);
    footer.appendChild(btnDone);

    // (Optional) dots
    const dotsBar = createEl('div', 'tut-dots');
    const dots = images.map((_,i)=> {
      const d = createEl('div','tut-dot' + (i===0?' is-active':'')); 
      dotsBar.appendChild(d); 
      return d;
    });
    frame.appendChild(dotsBar);

    let idx = 0;
    function update(){
      slides.forEach((s,i)=> s.classList.toggle('is-active', i===idx));
      dots.forEach((d,i)=> d.classList.toggle('is-active', i===idx));
      // 上一頁：第一張不顯示
      btnPrev.style.display = (idx===0) ? 'none' : '';
      // 下一頁：最後一張仍保留，但半透明，避免誤關
      btnNext.style.opacity = (idx===images.length-1) ? .5 : 1;
      // 「我知道了」只在最後一張顯示
      btnDone.style.display = (idx===images.length-1) ? 'inline-flex' : 'none';
    }

    function show(){
      if(!overlay.isConnected) document.body.appendChild(overlay);
      overlay.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      // 重置狀態回到第一張
      idx = 0;
      update();
      // 將焦點移到 overlay 以啟用鍵盤操作
      overlay.tabIndex = -1;
      overlay.focus();
    }
    function hide(){
      overlay.classList.remove('is-open');
      document.body.style.overflow = '';
    }
    function done(){
      localStorage.setItem(lsKey, '1'); // 只有按「我知道了」才標記已讀
      hide();
    }
    function clear(){
      localStorage.removeItem(lsKey);
    }

    // Events
    btnPrev.addEventListener('click', ()=>{ if(idx>0){ idx--; update(); } });
    btnNext.addEventListener('click', ()=>{
      if(idx < images.length-1){ idx++; update(); }
    });
    btnClose.addEventListener('click', hide);
    btnDone.addEventListener('click', done);

    if(enableEsc){
      overlay.addEventListener('keydown', (e)=>{
        if(e.key === 'Escape'){ hide(); }
        else if(e.key === 'ArrowLeft'){ if(idx>0){ idx--; update(); } }
        else if(e.key === 'ArrowRight'){ if(idx<images.length-1){ idx++; update(); } }
      });
    }

    // Auto show once (如果沒看過 && autoShow 為 true)
    if(autoShow && !seen){ show(); }

    // API
    return { show, hide, clear };
  }

  // export
  global.initImageTutorial = initImageTutorial;
})(window);
