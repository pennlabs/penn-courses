import { MapContainer, TileLayer } from "react-leaflet";
import Marker from "../map/Marker";

interface MapProps {
    lat: number;
    lng: number;
}

export default function Map({ lat, lng }: MapProps) {
    return (
        <MapContainer
            center={[lat, lng]}
            zoom={15}
            scrollWheelZoom={false}
            style={{ height: "100%", width: "100%" }}
        >
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker lat={lat} lng={lng} />
        </MapContainer>
    );
}
