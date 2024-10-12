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
        width: "100px";
    `;

    const MapContainer = styled.div`
        height: 100%;
        width: 60%;
        margin-right: 5px;
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
                <Map lat={lat} lng={lng} />
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
