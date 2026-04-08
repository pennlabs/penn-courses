import React from "react";
import styled from "styled-components";
import Map from "../map/Map";
import "leaflet/dist/leaflet.css";

interface MapModalProps {
    lat: number;
    lng: number;
    room: string;
    title: string;
}

const MapModal = ({ lat, lng, room, title }: MapModalProps) => {
    const MapModalContainer = styled.div`
        display: flex;
        height: 200px;
    `;

    const MapContainer = styled.div`
        height: 100%;
        width: 70%;
        margin-right: 10px;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);

        .leaflet-control-attribution {
            font-size: 9px;
            opacity: 0.6;
            padding: 1px 4px;
        }
    `;

    const MapInfoContainer = styled.ul`
        > *:not(:first-child) {
            margin-top: 5px;
        }
    `;

    const MapInfo = styled.li`
        > *:first-child {
            font-weight: bold;
        }
    `;

    return (
        <MapModalContainer>
            <MapContainer>
                <Map locations={[{ lat: lat, lng: lng }]} zoom={17} />
            </MapContainer>

            <MapInfoContainer>
                <MapInfo>
                    <div>Course</div>
                    <div>{title}</div>
                </MapInfo>
                <MapInfo>
                    <div>Loaction</div>
                    <div>{room}</div>
                </MapInfo>
                <MapInfo>
                    <div>View on Google Maps: </div>
                    <a
                        href={`https://maps.google.com/?q=${lat},${lng}`}
                        target="_blank"
                    >
                        Link
                    </a>
                </MapInfo>
            </MapInfoContainer>
        </MapModalContainer>
    );
};

export default MapModal;
