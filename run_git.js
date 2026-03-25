const { execSync } = require('child_process');
const path = require('path');

const dir = "C:\\Users\\HomePC\\Downloads\\nft_platform_backend-main (1)\\nft_platform_backend-main";
const commitMessage = `Fix complete NFT minting flow - image upload and database persistence

BACKEND FIXES:
- Fixed blockchain clients (TON, Solana, Ethereum) to return transaction_hash and token_id
- Fixed TON client parameter name: nft_data → nft_metadata
- Added mock transaction generation for development/testing

FRONTEND FIXES:
- Fixed handleMint function - was missing function declaration wrapper
- Added wallet connection step to get wallet_id before minting
- Fixed MintNFTRequest to include required wallet_id field
- Removed duplicate catch blocks (invalid JavaScript syntax)
- Added proper error handling with helpful messages
- Added form reset and preview clearing after successful mint

FLOW IMPROVEMENTS:
- Image now uploads and shows in preview immediately
- User sees clear button status at each step:
  'Connecting wallet...' → 'Uploading media...' → 'Minting NFT...'
- NFT minted successfully is immediately added to database
- User sees success alert with NFT ID and transaction hash
- Redirects to dashboard to view new NFT

FILES MODIFIED:
- app/blockchain/ton_client.py (transaction hash, parameter fix)
- app/blockchain/solana_client.py (transaction hash, token ID)
- app/blockchain/ethereum_client.py (transaction hash, token ID)
- app/static/webapp/mint.html (handleMint function, wallet logic)

TESTED FLOW:
✅ Image upload shows immediately in preview
✅ Database persistence working with await db.commit()
✅ All required fields in MintNFTRequest
✅ Blockchain clients return proper response format
✅ Error handling guides user to solutions

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`;

try {
  process.chdir(dir);
  
  console.log("===== GIT ADD -A =====");
  const addOutput = execSync('git add -A', { encoding: 'utf8' });
  console.log(addOutput || "(no output)");
  
  console.log("\n===== GIT COMMIT =====");
  const commitOutput = execSync(`git commit -m "${commitMessage.replace(/"/g, '\\"')}"`, { encoding: 'utf8' });
  console.log(commitOutput);
  
  console.log("\n===== GIT PUSH ORIGIN MAIN =====");
  const pushOutput = execSync('git push origin main', { encoding: 'utf8' });
  console.log(pushOutput);
  
  console.log("\n===== COMMANDS COMPLETED SUCCESSFULLY =====");
} catch (error) {
  console.error("Error executing git commands:");
  console.error(error.message);
  if (error.stdout) console.error("STDOUT:", error.stdout.toString());
  if (error.stderr) console.error("STDERR:", error.stderr.toString());
}
