import IntercityOfferDetailClient from "./IntercityOfferDetailClient";


export default async function IntercityOfferDetailPage({
  params,
}: {
  params: Promise<{ kind: string; id: string }>;
}) {
  const { kind, id } = await params;
  return <IntercityOfferDetailClient kind={kind} id={id} />;
}