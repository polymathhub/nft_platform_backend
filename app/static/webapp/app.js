(async function(){
  const statusEl = document.getElementById('status');
  const userEl = document.getElementById('user');
  const walletsEl = document.getElementById('wallets');
  const actionsEl = document.getElementById('actions');

  function show(el){ el.hidden = false }
  function hide(el){ el.hidden = true }
  function truncate(s){ return s && s.length>24 ? s.slice(0,10)+'…'+s.slice(-10) : s }

  statusEl.textContent = 'Checking Telegram context...';

  const initData = (window.Telegram && window.Telegram.WebApp && (window.Telegram.WebApp.initData || window.Telegram.WebApp.initDataUnsafe)) || '';
  if(!initData){ statusEl.textContent = 'Open this page from the Telegram app Web App button.'; return }

  statusEl.textContent = 'Authenticating...';
  try{
    const res = await fetch(`/api/v1/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
    const payload = await res.json();
    if(!payload.success){ statusEl.textContent = 'Authentication failed'; console.error(payload); return }

    const user = payload.user;
    statusEl.textContent = 'Authenticated';
    show(userEl); show(walletsEl); show(actionsEl);

    userEl.innerHTML = `<h2>${user.first_name || user.telegram_username}</h2><div class="muted">@${user.telegram_username || ''}</div>`;

    // load wallets
    const wres = await fetch(`/api/v1/wallets?user_id=${user.id}`);
    const wjson = await wres.json();
    if(!Array.isArray(wjson)){
      walletsEl.innerHTML = '<p class="muted">Failed to load wallets</p>';
    } else {
      renderWallets(wjson);
    }

    // actions
    actionsEl.innerHTML = '<div class="grid"><button id="createWallet" class="btn">Create Wallet</button><button id="importWallet" class="btn">Import Wallet</button></div>';
    document.getElementById('createWallet').addEventListener('click', showCreateSelector);
    document.getElementById('importWallet').addEventListener('click', showImportForm);

  }catch(e){ statusEl.textContent = 'Error: '+e.message; console.error(e) }

  function renderWallets(list){
    walletsEl.innerHTML = '<h3>Your wallets</h3>';
    if(list.length === 0){ walletsEl.innerHTML += '<p class="muted">No wallets yet.</p>'; return }
    const ul = document.createElement('ul');
    list.forEach(w=>{
      const li = document.createElement('li');
      li.innerHTML = `<div class="wallet-meta"><strong>${w.blockchain?.toUpperCase() || 'Wallet'}</strong><code>${truncate(w.address)}</code></div><div><button class="btn mint" data-id="${w.id}">MINT</button> <button class="btn" data-id="${w.id}" style="background:transparent;border:1px solid rgba(255,255,255,0.06);color:var(--muted);">DETAILS</button></div>`;
      ul.appendChild(li);
    });
    walletsEl.appendChild(ul);
    document.querySelectorAll('.mint').forEach(b=>b.addEventListener('click', onMintClick));
  }

  function onMintClick(e){ const walletId = e.currentTarget.dataset.id; showMintForm(walletId) }

  function showCreateSelector(){
    const markup = `<div class="card"><h4>Select blockchain</h4><div class="grid"> <button class="btn chain" data-chain="ethereum">Ethereum</button> <button class="btn chain" data-chain="polygon">Polygon</button> <button class="btn chain" data-chain="solana">Solana</button> <button class="btn chain" data-chain="ton">TON</button> </div></div>`;
    walletsEl.insertAdjacentHTML('beforeend', markup);
    document.querySelectorAll('.chain').forEach(btn=>btn.addEventListener('click', async ev=>{
      const chain = ev.currentTarget.dataset.chain;
      statusEl.textContent = `Creating ${chain} wallet...`;
      try{
        const form = new URLSearchParams();
        form.append('user_id', user.id);
        form.append('blockchain', chain);
        const resp = await fetch('/api/v1/wallets/create', {method:'POST', body: form});
        const j = await resp.json();
        if(j.success && j.wallet){
          statusEl.textContent = 'Wallet created';
          // reload wallets
          const wres2 = await fetch(`/api/v1/wallets?user_id=${user.id}`);
          renderWallets(await wres2.json());
        } else {
          statusEl.textContent = 'Failed to create wallet'; console.error(j);
        }
      }catch(er){ statusEl.textContent = 'Error: '+er.message }
    }))
  }

  function showImportForm(){
    const markup = `<div class="card"><h4>Import wallet</h4><div><input id="importAddr" placeholder="Address" style="width:100%;padding:8px;border-radius:8px;margin-bottom:8px"/></div><div><select id="importChain"><option value="ethereum">Ethereum</option><option value="solana">Solana</option></select></div><div style="margin-top:8px"><button id="doImport" class="btn">Import</button></div></div>`;
    walletsEl.insertAdjacentHTML('beforeend', markup);
    document.getElementById('doImport').addEventListener('click', async ()=>{
      const addr = document.getElementById('importAddr').value.trim(); const chain = document.getElementById('importChain').value;
      if(!addr){ alert('Enter address'); return }
      statusEl.textContent = 'Importing...';
      try{
        const body = { blockchain: chain, address: addr, name: `${chain} Imported` };
        const resp = await fetch(`/api/v1/wallets/import?user_id=${user.id}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const j = await resp.json();
        if(j && j.id){ statusEl.textContent = 'Imported'; const wres2 = await fetch(`/api/v1/wallets?user_id=${user.id}`); renderWallets(await wres2.json()) } else { statusEl.textContent = 'Import failed'; console.error(j) }
      }catch(er){ statusEl.textContent = 'Error: '+er.message }
    })
  }

  function showMintForm(walletId){
    const markup = `<div class="card"><h4>Mint NFT</h4><input id="nftName" placeholder="Name" style="width:100%;padding:8px;border-radius:8px;margin-bottom:8px"/><textarea id="nftDesc" placeholder="Description" style="width:100%;padding:8px;border-radius:8px;margin-bottom:8px"></textarea><div><button id="doMint" class="btn">Mint</button></div></div>`;
    walletsEl.insertAdjacentHTML('beforeend', markup);
    document.getElementById('doMint').addEventListener('click', async ()=>{
      const name = document.getElementById('nftName').value.trim(); const desc = document.getElementById('nftDesc').value.trim();
      if(!name){ alert('Enter a name'); return }
      statusEl.textContent = 'Minting...';
      try{
        const body = { user_id: user.id, wallet_id: walletId, nft_name: name, nft_description: desc };
        const resp = await fetch('/api/v1/telegram/web-app/mint', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const j = await resp.json();
        if(j && j.get('success')){ statusEl.textContent = 'Mint started'; } else { statusEl.textContent = 'Mint failed'; console.error(j) }
      }catch(er){ statusEl.textContent = 'Error: '+er.message }
    })
  }

})();
