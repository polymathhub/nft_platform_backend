(async function(){
  const statusEl = document.getElementById('status');
  const userEl = document.getElementById('user');
  const walletsEl = document.getElementById('wallets');
  const actionsEl = document.getElementById('actions');

  function show(el){ el.hidden = false; }
  function hide(el){ el.hidden = true; }
  function truncate(s){ return s && s.length > 32 ? s.slice(0, 14) + '…' + s.slice(-14) : s; }

  // Initialize Telegram WebApp
  if (window.Telegram && window.Telegram.WebApp) {
    window.Telegram.WebApp.ready();
  }

  statusEl.textContent = 'Checking Telegram context...';

  const initData = (window.Telegram && window.Telegram.WebApp && (window.Telegram.WebApp.initData || window.Telegram.WebApp.initDataUnsafe)) || '';
  if(!initData){ 
    statusEl.textContent = 'Open this link from the Telegram app using the "Open App" button.'; 
    statusEl.style.background = 'rgba(239, 68, 68, 0.1)';
    statusEl.style.borderColor = 'rgba(239, 68, 68, 0.2)';
    return; 
  }

  statusEl.textContent = 'Authenticating with NFT Platform...';
  
  try{
    const res = await fetch(`/api/v1/telegram/web-app/init?init_data=${encodeURIComponent(initData)}`);
    const payload = await res.json();
    
    if(!payload.success){ 
      statusEl.textContent = 'Authentication failed: ' + (payload.error || 'Unknown error'); 
      console.error(payload); 
      return; 
    }

    const user = payload.user;
    statusEl.textContent = 'Connected and ready to use NFT Platform';
    statusEl.style.background = 'rgba(16, 185, 129, 0.1)';
    statusEl.style.borderColor = 'rgba(16, 185, 129, 0.2)';
    
    // Show user section
    show(userEl);
    document.getElementById('userName').textContent = user.first_name || user.telegram_username || 'User';
    document.getElementById('userHandle').textContent = '@' + (user.telegram_username || 'anonymous');

    // Load wallets
    try{
      const wres = await fetch(`/api/v1/wallets?user_id=${user.id}`);
      const wjson = await wres.json();
      if(Array.isArray(wjson) && wjson.length > 0){
        show(walletsEl);
        renderWallets(wjson, user.id);
      } else {
        show(walletsEl);
        document.getElementById('walletsList').innerHTML = '<p class="muted">No wallets yet. Create one to get started.</p>';
      }
    } catch(er){
      console.error('Failed to load wallets:', er);
      show(walletsEl);
      document.getElementById('walletsList').innerHTML = '<p class="muted">Unable to load wallets. Please try again.</p>';
    }

    // Show actions
    show(actionsEl);
    setupActionButtons(user.id);

  } catch(e){ 
    statusEl.textContent = 'Error: ' + e.message; 
    statusEl.style.background = 'rgba(239, 68, 68, 0.1)';
    statusEl.style.borderColor = 'rgba(239, 68, 68, 0.2)';
    console.error('Initialization error:', e);
  }

  function renderWallets(list, userId){
    if(list.length === 0){ 
      document.getElementById('walletsList').innerHTML = '<p class="muted">No wallets yet. Create one to get started.</p>'; 
      return; 
    }
    
    const ul = document.createElement('ul');
    ul.className = 'wallets-grid';
    
    list.forEach(w => {
      const li = document.createElement('li');
      li.className = 'wallet-item';
      li.innerHTML = `
        <div class="wallet-meta">
          <strong>${w.blockchain ? w.blockchain.toUpperCase() : 'Wallet'}</strong>
          <code>${truncate(w.address)}</code>
        </div>
        <div class="wallet-actions">
          <button class="btn mint" data-id="${w.id}">Mint</button>
          <button class="btn secondary details" data-id="${w.id}">Details</button>
        </div>
      `;
      ul.appendChild(li);
    });
    
    document.getElementById('walletsList').innerHTML = '';
    document.getElementById('walletsList').appendChild(ul);
    
    document.querySelectorAll('.mint').forEach(b => {
      b.addEventListener('click', onMintClick);
    });
    
    document.querySelectorAll('.details').forEach(b => {
      b.addEventListener('click', (e) => {
        alert('Wallet details: ' + e.currentTarget.dataset.id);
      });
    });
  }

  function onMintClick(e){ 
    const walletId = e.currentTarget.dataset.id; 
    showMintForm(walletId); 
  }

  function setupActionButtons(userId){
    const createBtn = document.getElementById('createWallet');
    const importBtn = document.getElementById('importWallet');
    const browseBtn = document.getElementById('browseNFTs');
    const marketplaceBtn = document.getElementById('viewMarketplace');
    
    if(createBtn) createBtn.addEventListener('click', () => showCreateSelector(userId));
    if(importBtn) importBtn.addEventListener('click', () => showImportForm(userId));
    if(browseBtn) browseBtn.addEventListener('click', () => { 
      statusEl.textContent = 'Browsing NFTs...'; 
      alert('NFT browsing coming soon'); 
    });
    if(marketplaceBtn) marketplaceBtn.addEventListener('click', () => { 
      statusEl.textContent = 'Loading Marketplace...'; 
      alert('Marketplace coming soon'); 
    });
  }

  function showCreateSelector(userId){
    const modal = document.createElement('div');
    modal.className = 'card';
    modal.style.marginTop = '12px';
    modal.innerHTML = `
      <h4>Select Blockchain</h4>
      <div class="grid">
        <button class="btn chain" data-chain="ethereum">Ethereum</button>
        <button class="btn chain" data-chain="polygon">Polygon</button>
        <button class="btn chain" data-chain="solana">Solana</button>
        <button class="btn chain" data-chain="ton">TON</button>
      </div>
    `;
    walletsEl.appendChild(modal);
    
    document.querySelectorAll('.chain').forEach(btn => {
      btn.addEventListener('click', async ev => {
        const chain = ev.currentTarget.dataset.chain;
        statusEl.textContent = `Creating ${chain.charAt(0).toUpperCase() + chain.slice(1)} wallet...`;
        try{
          const form = new URLSearchParams();
          form.append('user_id', userId);
          form.append('blockchain', chain);
          const resp = await fetch('/api/v1/wallets/create', {method:'POST', body: form});
          const j = await resp.json();
          if(j.success && j.wallet){
            statusEl.textContent = 'Wallet created successfully!';
            modal.remove();
            // Reload wallets
            const wres2 = await fetch(`/api/v1/wallets?user_id=${userId}`);
            const wallets = await wres2.json();
            if(Array.isArray(wallets)) renderWallets(wallets, userId);
          } else {
            statusEl.textContent = 'Failed to create wallet'; 
            console.error(j);
          }
        } catch(er){ 
          statusEl.textContent = 'Error: ' + er.message;
        }
      });
    });
  }

  function showImportForm(userId){
    const modal = document.createElement('div');
    modal.className = 'card';
    modal.style.marginTop = '12px';
    modal.innerHTML = `
      <h4>Import Wallet</h4>
      <input id="importAddr" type="text" placeholder="Wallet address" />
      <select id="importChain" style="margin-top: 8px;">
        <option value="ethereum">Ethereum</option>
        <option value="solana">Solana</option>
        <option value="polygon">Polygon</option>
        <option value="ton">TON</option>
      </select>
      <div style="margin-top: 12px;">
        <button id="doImport" class="btn" style="width: 100%;">Import Wallet</button>
        <button id="cancelImport" class="btn secondary" style="width: 100%; margin-top: 6px;">Cancel</button>
      </div>
    `;
    walletsEl.appendChild(modal);
    
    document.getElementById('cancelImport').addEventListener('click', () => modal.remove());
    
    document.getElementById('doImport').addEventListener('click', async () => {
      const addr = document.getElementById('importAddr').value.trim();
      const chain = document.getElementById('importChain').value;
      if(!addr){ 
        statusEl.textContent = 'Please enter a wallet address';
        return; 
      }
      statusEl.textContent = 'Importing wallet...';
      try{
        const body = { blockchain: chain, address: addr, name: `${chain} Imported` };
        const resp = await fetch(`/api/v1/wallets/import?user_id=${userId}`, {
          method:'POST', 
          headers:{'Content-Type':'application/json'}, 
          body: JSON.stringify(body)
        });
        const j = await resp.json();
        if(j && j.id){ 
          statusEl.textContent = 'Wallet imported successfully!';
          modal.remove();
          const wres2 = await fetch(`/api/v1/wallets?user_id=${userId}`);
          const wallets = await wres2.json();
          if(Array.isArray(wallets)) renderWallets(wallets, userId);
        } else { 
          statusEl.textContent = 'Import failed'; 
          console.error(j);
        }
      } catch(er){ 
        statusEl.textContent = 'Error: ' + er.message;
      }
    });
  }

  function showMintForm(walletId){
    const modal = document.createElement('div');
    modal.className = 'card';
    modal.style.marginTop = '12px';
    modal.innerHTML = `
      <h4>Mint NFT</h4>
      <input id="nftName" type="text" placeholder="NFT name" />
      <textarea id="nftDesc" placeholder="Description" style="margin-top: 8px; min-height: 80px;"></textarea>
      <div style="margin-top: 12px;">
        <button id="doMint" class="btn" style="width: 100%;">Mint NFT</button>
        <button id="cancelMint" class="btn secondary" style="width: 100%; margin-top: 6px;">Cancel</button>
      </div>
    `;
    walletsEl.appendChild(modal);
    
    document.getElementById('cancelMint').addEventListener('click', () => modal.remove());
    document.getElementById('doMint').addEventListener('click', () => {
      const name = document.getElementById('nftName').value.trim();
      const desc = document.getElementById('nftDesc').value.trim();
      if(!name){ 
        statusEl.textContent = 'Please enter an NFT name';
        return; 
      }
      statusEl.textContent = 'Minting NFT...';
      alert('Minting ' + name + ' — Feature coming soon!');
      modal.remove();
    });
  }

})();
