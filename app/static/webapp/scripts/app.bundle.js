/* app.bundle.js — lightweight app bootstrap and compatibility layer
   Restores core functions used by inline handlers and enables basic interactivity.
*/
(function(){
  'use strict';

  // Simple API wrapper
  const Api = {
    base: '/api/v1',
    getToken() {
      try { return localStorage.getItem('jwt_access_token'); } catch { return null; }
    },
    setToken(t) { try { if (t) localStorage.setItem('jwt_access_token', t); else localStorage.removeItem('jwt_access_token'); } catch {} },
    async call(method, path, body = null) {
      const url = path.startsWith('/') ? path : `${this.base}/${path}`;
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      const token = this.getToken();
      if (token) opts.headers['Authorization'] = `Bearer ${token}`;
      if (body) opts.body = JSON.stringify(body);
      try {
        const res = await fetch(url, opts);
        const text = await res.text();
        let data = text;
        try { data = JSON.parse(text); } catch {}
        return { ok: res.ok, status: res.status, data };
      } catch (e) {
        return { ok: false, status: 0, error: e.message };
      }
    }
  };

  // Wallet manager (minimal)
  const WalletManager = {
    connected: null,
    wallets: [],
    isConnected() { return !!this.connected; },
    setConnected(w) { this.connected = w; try { localStorage.setItem('connected_wallet', JSON.stringify(w)); } catch {} },
    setAll(ws) { this.wallets = ws || []; try { localStorage.setItem('connected_wallets', JSON.stringify(this.wallets)); } catch {} },
    load() { try { const s = localStorage.getItem('connected_wallet'); if (s) this.connected = JSON.parse(s); } catch {} }
  };

  // Minimal UI helpers
  function showStatus(msg, type='info'){
    let toast = document.getElementById('appToast');
    if (!toast) { toast = document.createElement('div'); toast.id='appToast'; document.body.appendChild(toast); }
    toast.textContent = msg;
    toast.style.position='fixed'; toast.style.right='16px'; toast.style.bottom='16px'; toast.style.padding='10px 14px'; toast.style.borderRadius='8px';
    toast.style.background = type==='error'? '#ef4444' : type==='success'? '#10b981':'#3b82f6';
    toast.style.color = 'white';
    setTimeout(()=>{ try{ toast.remove(); }catch{} }, 3500);
  }

  // App object with methods referenced by inline handlers
  const App = {
    state: { activeView: 'home' },
    switchPage(view){
      try{
        const map = {
          'home': 'dashboardContent',
          'wallet': 'walletContent',
          'mint': 'mintContent',
          'market': 'marketplaceContent',
          'collectionDetails': 'collectionDetailsContent',
          'nftDetail': 'nftDetailContent',
          'myListings': 'myListingsContent',
          'profile': 'profileContent'
        };
        Object.values(map).forEach(id => { const el = document.getElementById(id); if (el) el.style.display='none'; });
        const showId = map[view] || 'dashboardContent';
        const showEl = document.getElementById(showId);
        if (showEl) showEl.style.display = 'block';
        // nav active class
        document.querySelectorAll('.nav-item').forEach(it=>it.classList.toggle('active', (it.dataset.view||it.getAttribute('data-view'))===view));
        this.state.activeView = view;
      }catch(e){ console.error('[App.switchPage]', e); }
    },

    viewCollectionDetails(id){
      window.currentCollection = id; this.switchPage('collectionDetails');
      showStatus('Loading collection...', 'info');
      // Try to fetch collection details (best-effort)
      Api.call('GET', `/api/v1/collections/${id}`).then(r=>{ if(r.ok) showStatus('Collection loaded', 'success'); else showStatus('Collection not available', 'error'); });
    },

    viewNFTDetail(id){ window.selectedNFTId = id; this.switchPage('nftDetail'); setTimeout(()=>{ this.loadNFTDetail && this.loadNFTDetail(); }, 100); },

    async loadNFTDetail(){
      try{
        const nftId = window.selectedNFTId; if(!nftId) return;
        const res = await Api.call('GET', `/api/v1/nft/${nftId}`);
        if (res.ok && res.data){
          document.getElementById('nftDetailName').textContent = res.data.name || 'NFT';
          // set image
          const el = document.getElementById('nftDetailImage'); if (el && res.data.image_url) el.innerHTML = `<img src="${res.data.image_url}" style="width:100%;height:100%;object-fit:cover">`;
        } else {
          showStatus('Failed to load NFT', 'error');
        }
      }catch(e){ console.error(e); showStatus('Error loading NFT', 'error'); }
    },

    async buyNFTFromDetail(){
      try{
        const nft = window.currentNFTDetail || {};
        if(!WalletManager.isConnected()) { showStatus('Connect wallet first', 'warning'); return; }
        showStatus('Initiating purchase...', 'info');
        // Best-effort POST to marketplace buy
        const res = await Api.call('POST', `/api/v1/marketplace/listings/${nft.listing_id || ''}/buy`, { amount: nft.price || 0 });
        if(res.ok) showStatus('Purchase initiated', 'success'); else showStatus('Purchase failed', 'error');
      }catch(e){ console.error(e); showStatus('Purchase error', 'error'); }
    },

    showPaymentSection(section){ showStatus('Showing payment: '+section, 'info'); /* toggle UI if present */ },

    async submitMintNFT(){
      try{
        const name = document.getElementById('mintName')?.value || '';
        const price = document.getElementById('mintPrice')?.value || '0';
        if(!name) { showStatus('Enter NFT name', 'error'); return; }
        showStatus('Minting...', 'info');
        const res = await Api.call('POST', '/api/v1/nft/mint', { name, price: parseFloat(price) });
        if(res.ok) showStatus('Minted', 'success'); else showStatus('Mint failed', 'error');
      }catch(e){ console.error(e); showStatus('Mint error', 'error'); }
    }
  };

  // Expose to window for existing inline handlers
  window.API = Api;
  window.WalletManager = WalletManager;
  window.app = App;
  window.switchPage = (v) => App.switchPage(v);
  window.initiateWalletConnection = async function(blockchain){ showStatus('Initiate connection: '+blockchain, 'info'); /* best-effort POST */ try{ const r = await Api.call('POST', `/api/v1/wallets/connect`, { wallet_type: blockchain, public_key: 'dev' }); if(r.ok) { WalletManager.setConnected(r.data || { address: 'dev' }); showStatus('Wallet connected', 'success'); } else showStatus('Connect failed', 'error'); }catch(e){ showStatus('Connection error', 'error'); } };
  window.showWalletConnectModal = function(){ showStatus('Open wallet modal', 'info'); /* simple modal */ const m = document.getElementById('modal'); if (m) m.innerHTML = '<div style="padding:20px;color:#fff">Connect wallet (dev)</div>'; document.getElementById('modalOverlay').classList.add('active'); };

  // Initialize basic interactivity
  function bootstrap(){
    try{
      WalletManager.load();
      // Hook nav items
      document.querySelectorAll('.nav-item').forEach(item=>{
        item.addEventListener('click',(e)=>{ e.preventDefault(); const view = item.dataset.view || item.getAttribute('data-view'); if(view) App.switchPage(view); });
      });

      // Ensure default view visible
      App.switchPage('home');

      // Attach buy buttons inside marketplace grid (if present)
      document.body.addEventListener('click', (e)=>{
        const t = e.target.closest('[data-action]');
        if(!t) return;
        const action = t.dataset.action;
        if(action === 'buy-now') { App.buyNFTFromDetail(); }
      });

      console.log('[app.bundle] initialized');
    }catch(e){ console.error('[app.bundle] bootstrap error', e); }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootstrap); else bootstrap();

})();
