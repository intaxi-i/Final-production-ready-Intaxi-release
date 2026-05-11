export type DonationWallet = {
  key: string;
  title: string;
  network: string;
  asset: string;
  address: string;
  warning?: string;
};

export const DONATION_WALLETS: DonationWallet[] = [
  {
    key: 'btc',
    title: 'Bitcoin',
    network: 'Bitcoin',
    asset: 'BTC',
    address: 'bc1q82r5z009xkpcpr4kacp9rfwehc04m424ukj9gw',
  },
  {
    key: 'eth',
    title: 'Ethereum',
    network: 'Ethereum ERC20',
    asset: 'ETH',
    address: '0x3F8e546cEc1871722d370D7126A8465BA86972Ec',
  },
  {
    key: 'sol',
    title: 'Solana',
    network: 'Solana',
    asset: 'SOL',
    address: 'FcN1drzzy3QWD1tdGzJmamK1QojMkQVt5NeLMPY8yyZG',
  },
  {
    key: 'trx',
    title: 'Tron',
    network: 'Tron TRC20',
    asset: 'TRX',
    address: 'TWK5r3JmbjGsrrjqDY7XQyKUjtiXhDAaL6',
  },
  {
    key: 'usdt-trc20',
    title: 'USDT',
    network: 'TRC20',
    asset: 'USDT',
    address: 'TWK5r3JmbjGsrrjqDY7XQyKUjtiXhDAaL6',
    warning: 'Отправляйте USDT только через сеть TRC20.',
  },
];

export function walletFingerprint(address: string) {
  if (address.length <= 16) return address;
  return `${address.slice(0, 8)}...${address.slice(-8)}`;
}
