import CityOfferDetailClient from "./CityOfferDetailClient";

export const runtime = "edge";

export default async function CityOfferDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CityOfferDetailClient id={id} />;
}
