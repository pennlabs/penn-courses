import React from "react";
import { Marker as MarkerLeaflet } from "react-leaflet";
// @ts-ignore
import { divIcon } from "leaflet";

interface MarkerProps {
    lat: number;
    lng: number;
    color?: string;
}

const Marker = ({ color = "#878ED8", lat, lng }: MarkerProps) => {
    const icon = divIcon({
        // @ts-ignore
        html: `
                <svg
                  width="20"
                  height="28"
                  viewBox="0 0 20 28"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M10 13.3C9.0528 13.3 8.14439 12.9313 7.47462 12.2749C6.80485 11.6185 6.42857 10.7283 6.42857 9.8C6.42857 8.87174 6.80485 7.9815 7.47462 7.32513C8.14439 6.66875 9.0528 6.3 10 6.3C10.9472 6.3 11.8556 6.66875 12.5254 7.32513C13.1952 7.9815 13.5714 8.87174 13.5714 9.8C13.5714 10.2596 13.4791 10.7148 13.2996 11.1394C13.1201 11.564 12.857 11.9499 12.5254 12.2749C12.1937 12.5999 11.8 12.8577 11.3667 13.0336C10.9334 13.2095 10.469 13.3 10 13.3ZM10 0C7.34784 0 4.8043 1.0325 2.92893 2.87035C1.05357 4.70821 0 7.20088 0 9.8C0 17.15 10 28 10 28C10 28 20 17.15 20 9.8C20 7.20088 18.9464 4.70821 17.0711 2.87035C15.1957 1.0325 12.6522 0 10 0Z"
                    fill="${color}"
                  />
                </svg>
              `,
        className: "svg-icon",
        iconSize: [24, 40],
        iconAnchor: [12, 40],
    });

    return (
        <MarkerLeaflet
            // @ts-ignore
            position={[lat, lng]}
            icon={icon}
        />
    );
};

export default React.memo(Marker);
