const fs=require('fs');const N=+fs.readFileSync(0,'utf8').trim();if(N<2){console.log(0);process.exit(0)}
const m=new Uint8Array((N>>1)+1);let c=1;for(let p=3;p*p<=N;p+=2){if(!m[p>>1]){for(let j=p*p;j<=N;j+=p<<1)m[j>>1]=1}}
for(let i=3;i<=N;i+=2)if(!m[i>>1])c++;console.log(c);
