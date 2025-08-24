/*! img_tutorial.js — Shared, image-based first-visit tutorial (v1.1) */
(function(global){
  const registry = new Map(); // pageKey -> state

  function storageKey(version, pageKey){ return `imgTutorialSeen:${version}:${pageKey}`; }
  function hasSeen(key){ try { return localStorage.getItem(key)==='1'; } catch(e){ return document.cookie.split('; ').some(v=>v.startsWith(encodeURIComponent(key)+'=1')); } }
  function markSeen(key){ try { localStorage.setItem(key,'1'); } catch(e){ document.cookie = encodeURIComponent(key)+'=1; path=/; max-age=31536000'; } }
  function clearSeen(key){ try { localStorage.removeItem(key); } catch(e){} document.cookie = encodeURIComponent(key)+'=; path=/; max-age=0'; }

  function preload(srcs){ srcs.forEach(s => { const i = new Image(); i.src = s; }); }

  function createDOM(){
    const root = document.createElement('div');
    root.id = 'imgTutorial';
    root.className = 'imgtut hidden';
    root.setAttribute('role','dialog');
    root.setAttribute('aria-modal','true');
    root.setAttribute('aria-labelledby','imgTutCounter');

    const frame = document.createElement('div');
    frame.className = 'imgtut__frame';

    const counter = document.createElement('span');
    counter.id = 'imgTutCounter';
    counter.className = 'imgtut__counter';
    counter.setAttribute('aria-live','polite');
    counter.textContent = '1/1';

    const img = document.createElement('img');
    img.id = 'imgTutImage';
    img.className = 'imgtut__img';
    img.alt = '教學圖片 1/1';

    const nav = document.createElement('div');
    nav.className = 'imgtut__nav';

    const prev = document.createElement('button');
    prev.id = 'imgTutPrev';
    prev.className = 'imgtut__btn imgtut__btn--prev';
    prev.setAttribute('aria-label','上一頁');
    prev.textContent = '‹';

    const next = document.createElement('button');
    next.id = 'imgTutNext';
    next.className = 'imgtut__btn imgtut__btn--next';
    next.setAttribute('aria-label','下一頁');
    next.textContent = '›';

    const done = document.createElement('button');
    done.id = 'imgTutDone';
    done.className = 'imgtut__btn imgtut__btn--done';
    done.setAttribute('aria-label','我知道了');
    done.textContent = '我知道了';

    nav.appendChild(prev); nav.appendChild(next); nav.appendChild(done);
    frame.appendChild(counter); frame.appendChild(img); frame.appendChild(nav);
    root.appendChild(frame);
    document.body.appendChild(root);
    return {root, frame, counter, img, next, prev, done};
  }

  function initImageTutorial(opts){
    const {
      pageKey,
      images = [],      // array of absolute URLs
      version = 'img-v1',
      autoShow = true,
      enableEsc = true,
      onDone = null
    } = opts || {};
    if(!pageKey) { console.warn('[img_tutorial] Missing pageKey'); return; }
    if(!images.length) { console.warn('[img_tutorial] images is empty'); return; }

    let nodes;
    if(document.getElementById('imgTutorial')){
      nodes = {
        root: document.getElementById('imgTutorial'),
        frame: document.querySelector('.imgtut__frame'),
        counter: document.getElementById('imgTutCounter'),
        img: document.getElementById('imgTutImage'),
        next: document.getElementById('imgTutNext'),
        prev: document.getElementById('imgTutPrev'),
        done: document.getElementById('imgTutDone')
      };
    } else {
      nodes = createDOM();
    }

    const key = storageKey(version, pageKey);
    let idx = 0, lastFocus=null, prevOverflow='';

    function onKeydown(e){
      if(e.key === 'ArrowRight' || e.key === 'Enter') handleNext();
      else if(e.key === 'ArrowLeft') handlePrev();
      else if(e.key === 'Escape' && enableEsc){ clearSeen(key); hide(false); }
    }
    function render(){
      nodes.img.src = images[idx];
      nodes.img.alt = `教學圖片 ${idx+1}/${images.length}`;
      nodes.counter.textContent = `${idx+1}/${images.length}`;
      // Prev visible only when not first
      nodes.prev.style.visibility = (idx > 0) ? 'visible' : 'hidden';
      // Next visible until last
      nodes.next.style.display = (idx === images.length - 1) ? 'none' : 'inline-block';
      // Done only on last
      nodes.done.style.display = (idx === images.length - 1) ? 'inline-block' : 'none';
      if(idx === images.length - 1){ nodes.done.focus({preventScroll:true}); }
    }
    function handleNext(){ if(idx < images.length - 1){ idx++; render(); nodes.next.focus({preventScroll:true}); } }
    function handlePrev(){ if(idx > 0){ idx--; render(); nodes.prev.focus({preventScroll:true}); } }
    function hide(mark=true){
      nodes.root.classList.add('hidden');
      document.body.style.overflow = prevOverflow || '';
      document.removeEventListener('keydown', onKeydown);
      if(mark) markSeen(key);
      if(lastFocus && lastFocus.focus){ try{ lastFocus.focus({preventScroll:true}); }catch(_){ } }
      if(mark && typeof onDone === 'function'){ try{ onDone(); }catch(_){ } }
    }
    function show(){
      lastFocus = document.activeElement;
      prevOverflow = document.body.style.overflow;
      nodes.root.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      idx = 0; render();
      nodes.next.focus({preventScroll:true});
      document.addEventListener('keydown', onKeydown);
    }

    nodes.next.onclick = handleNext;
    nodes.prev.onclick = handlePrev;
    nodes.done.onclick = () => hide(true);

    preload(images);

    const state = { show, hide, clear: () => clearSeen(key), key, pageKey, version };
    registry.set(pageKey, state);

    if(autoShow && !hasSeen(key)) show();
    return state;
  }

  function resetImageTutorial(pageKey){
    for(const [, st] of registry){
      if(!pageKey || st.pageKey === pageKey){ try{ localStorage.removeItem(st.key); }catch(e){} document.cookie = encodeURIComponent(st.key)+'=; path=/; max-age=0'; }
    }
  }

  // expose
  global.initImageTutorial = initImageTutorial;
  global.resetImageTutorial = resetImageTutorial;
})(window);