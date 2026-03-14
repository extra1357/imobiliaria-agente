(function() {
  const style = document.createElement('style');
  style.textContent = `
    #sofia-launcher {
      position: fixed;
      bottom: 28px;
      right: 28px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 12px;
    }

    #sofia-toggle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #c9a84c, #b8913e);
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 24px rgba(201,168,76,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      animation: sofia-pulse 3s ease-in-out infinite;
      transition: transform 0.2s;
      font-size: 26px;
    }
    #sofia-toggle:hover { transform: scale(1.1); }

    #sofia-badge {
      position: absolute;
      top: 2px;
      right: 2px;
      width: 13px;
      height: 13px;
      background: #22c55e;
      border-radius: 50%;
      border: 2px solid white;
    }

    .sofia-actions {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 10px;
      transition: all 0.3s ease;
      opacity: 0;
      pointer-events: none;
      transform: translateY(10px);
    }
    .sofia-actions.open {
      opacity: 1;
      pointer-events: all;
      transform: translateY(0);
    }

    .sofia-action-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 18px;
      border-radius: 50px;
      border: none;
      cursor: pointer;
      font-family: Arial, sans-serif;
      font-size: 14px;
      font-weight: 500;
      white-space: nowrap;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      transition: transform 0.2s, box-shadow 0.2s;
      text-decoration: none;
      color: white;
    }
    .sofia-action-btn:hover {
      transform: translateX(-4px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }

    .sofia-action-btn.sofia  { background: linear-gradient(135deg, #1a2235, #0f172a); border: 1px solid #c9a84c; color: #e8c97a; }
    .sofia-action-btn.whats  { background: linear-gradient(135deg, #25d366, #128c3e); }
    .sofia-action-btn.leads  { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }

    .sofia-action-icon { font-size: 18px; }

    #sofia-frame {
      position: fixed;
      bottom: 104px;
      right: 28px;
      width: 420px;
      height: 600px;
      border-radius: 20px;
      border: none;
      box-shadow: 0 8px 48px rgba(0,0,0,0.35);
      z-index: 9998;
      display: none;
    }
    #sofia-frame.open { display: block; }

    @keyframes sofia-pulse {
      0%,100% { box-shadow: 0 4px 24px rgba(201,168,76,0.4); }
      50%      { box-shadow: 0 4px 36px rgba(201,168,76,0.7); }
    }

    @media (max-width: 480px) {
      #sofia-frame {
        width: 100vw;
        height: 100vh;
        bottom: 0;
        right: 0;
        border-radius: 0;
      }
      #sofia-launcher { bottom: 16px; right: 16px; }
    }
  `;
  document.head.appendChild(style);

  // Container principal
  const launcher = document.createElement('div');
  launcher.id = 'sofia-launcher';

  // Ações
  const actions = document.createElement('div');
  actions.className = 'sofia-actions';
  actions.innerHTML = `
    <button class="sofia-action-btn sofia" id="sofia-chat-btn">
      <span class="sofia-action-icon">🤖</span> Sofia — Buscar Imóvel
    </button>
    <a class="sofia-action-btn whats"
       href="https://wa.me/5511976661297?text=Olá! Vim pelo site ImobiliáriaPerto e gostaria de mais informações."
       target="_blank">
      <span class="sofia-action-icon">💬</span> WhatsApp
    </a>
    <a class="sofia-action-btn leads"
       href="https://www.imobiliariaperto.com.br/admin/leads"
       target="_blank">
      <span class="sofia-action-icon">📋</span> Fale Conosco
    </a>
  `;

  // Botão toggle
  const toggle = document.createElement('button');
  toggle.id = 'sofia-toggle';
  toggle.title = 'Atendimento';
  toggle.innerHTML = `
    <svg viewBox="0 0 72 72" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="sw2" cx="50%" cy="35%" r="65%">
          <stop offset="0%" stop-color="#f7cfa0"/>
          <stop offset="100%" stop-color="#d4915c"/>
        </radialGradient>
      </defs>
      <ellipse cx="36" cy="70" rx="22" ry="14" fill="#1a2235"/>
      <rect x="31" y="50" width="10" height="10" rx="5" fill="url(#sw2)"/>
      <ellipse cx="36" cy="33" rx="15" ry="17" fill="url(#sw2)"/>
      <ellipse cx="36" cy="17" rx="17" ry="12" fill="#1e0d04"/>
      <ellipse cx="21" cy="33" rx="3" ry="5" fill="#d4a070"/>
      <ellipse cx="51" cy="33" rx="3" ry="5" fill="#d4a070"/>
      <ellipse cx="29" cy="33" rx="3.5" ry="4" fill="white"/>
      <ellipse cx="43" cy="33" rx="3.5" ry="4" fill="white"/>
      <circle cx="30" cy="33.5" r="2" fill="#5c3a1e"/>
      <circle cx="44" cy="33.5" r="2" fill="#5c3a1e"/>
      <path d="M29 43 Q36 48 43 43" stroke="#c04535" stroke-width="2" fill="none" stroke-linecap="round"/>
    </svg>
    <div id="sofia-badge"></div>
  `;

  // iframe Sofia
  const frame = document.createElement('iframe');
  frame.id = 'sofia-frame';
  frame.src = 'https://imobiliaria-agente2.vercel.app';

  launcher.appendChild(actions);
  launcher.appendChild(toggle);
  document.body.appendChild(launcher);
  document.body.appendChild(frame);

  // Toggle menu
  let menuOpen = false;
  let chatOpen = false;

  toggle.addEventListener('click', () => {
    menuOpen = !menuOpen;
    actions.classList.toggle('open', menuOpen);
    toggle.innerHTML = menuOpen
      ? `<span style="font-size:22px;color:#0a0f1e">✕</span>`
      : `<svg viewBox="0 0 72 72" width="32" height="32" xmlns="http://www.w3.org/2000/svg">
          <defs><radialGradient id="sw3" cx="50%" cy="35%" r="65%">
            <stop offset="0%" stop-color="#f7cfa0"/><stop offset="100%" stop-color="#d4915c"/>
          </radialGradient></defs>
          <ellipse cx="36" cy="70" rx="22" ry="14" fill="#1a2235"/>
          <rect x="31" y="50" width="10" height="10" rx="5" fill="url(#sw3)"/>
          <ellipse cx="36" cy="33" rx="15" ry="17" fill="url(#sw3)"/>
          <ellipse cx="36" cy="17" rx="17" ry="12" fill="#1e0d04"/>
          <ellipse cx="21" cy="33" rx="3" ry="5" fill="#d4a070"/>
          <ellipse cx="51" cy="33" rx="3" ry="5" fill="#d4a070"/>
          <ellipse cx="29" cy="33" rx="3.5" ry="4" fill="white"/>
          <ellipse cx="43" cy="33" rx="3.5" ry="4" fill="white"/>
          <circle cx="30" cy="33.5" r="2" fill="#5c3a1e"/>
          <circle cx="44" cy="33.5" r="2" fill="#5c3a1e"/>
          <path d="M29 43 Q36 48 43 43" stroke="#c04535" stroke-width="2" fill="none" stroke-linecap="round"/>
        </svg><div id="sofia-badge"></div>`;
    // fecha chat se abrir menu
    if (menuOpen && chatOpen) {
      frame.classList.remove('open');
      chatOpen = false;
    }
  });

  // Abre chat da Sofia
  document.getElementById('sofia-chat-btn').addEventListener('click', () => {
    chatOpen = !chatOpen;
    frame.classList.toggle('open', chatOpen);
    menuOpen = false;
    actions.classList.remove('open');
  });

  // Fecha clicando fora
  document.addEventListener('click', (e) => {
    if (!launcher.contains(e.target) && !frame.contains(e.target)) {
      menuOpen = false;
      chatOpen = false;
      actions.classList.remove('open');
      frame.classList.remove('open');
    }
  });
})();
