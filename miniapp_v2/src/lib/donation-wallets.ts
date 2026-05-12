export type DonationWallet = {
  key: string;
  title: string;
  network: string;
  asset: string;
  address: string;
  checksum: string;
  warning?: string;
};

export const DONATION_WALLETS: DonationWallet[] = [
  {
    key: 'btc',
    title: 'Bitcoin',
    network: 'Bitcoin',
    asset: 'BTC',
    address: 'bc1q82r5z009xkpcpr4kacp9rfwehc04m424ukj9gw',
    checksum: 'BTC-82R5-J9GW-42',
  },
  {
    key: 'eth',
    title: 'Ethereum',
    network: 'Ethereum ERC20',
    asset: 'ETH',
    address: '0x3F8e546cEc1871722d370D7126A8465BA86972Ec',
    checksum: 'ETH-3F8E-72EC-42',
  },
  {
    key: 'sol',
    title: 'Solana',
    network: 'Solana',
    asset: 'SOL',
    address: 'FcN1drzzy3QWD1tdGzJmamK1QojMkQVt5NeLMPY8yyZG',
    checksum: 'SOL-FCN1-YYZG-44',
  },
  {
    key: 'trx',
    title: 'Tron',
    network: 'Tron TRC20',
    asset: 'TRX',
    address: 'TWK5r3JmbjGsrrjqDY7XQyKUjtiXhDAaL6',
    checksum: 'TRX-TWK5-AAL6-34',
  },
  {
    key: 'usdt-trc20',
    title: 'USDT',
    network: 'TRC20',
    asset: 'USDT',
    address: 'TWK5r3JmbjGsrrjqDY7XQyKUjtiXhDAaL6',
    checksum: 'USDT-TWK5-AAL6-34',
    warning: 'Отправляйте USDT только через сеть TRC20. Адрес TRON и USDT TRC20 совпадает намеренно.',
  },
];

export function walletFingerprint(address: string) {
  if (address.length <= 16) return address;
  return `${address.slice(0, 8)}...${address.slice(-8)}`;
}

export function walletChunks(address: string) {
  return address.match(/.{1,4}/g)?.join(' ') || address;
}
