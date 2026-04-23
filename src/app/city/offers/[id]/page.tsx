import CityOfferDetailClient from "./CityOfferDetailClient";


export default async function CityOfferDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CityOfferDetailClient id={id} />;
}