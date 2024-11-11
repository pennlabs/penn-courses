import React, { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import Marker from "../map/Marker";
import { Location } from "../../types";

interface MapProps {
    locations: Location[];
    zoom: number;
}

function toRadians(degrees: number): number {
    return degrees * (Math.PI / 180);
}

function toDegrees(radians: number): number {
    return radians * (180 / Math.PI);
}

function getGeographicCenter(
    locations: Location[]
): [number, number] {
    let x = 0;
    let y = 0;
    let z = 0;

    locations.forEach((coord) => {
        const lat = toRadians(coord.lat);
        const lon = toRadians(coord.lng);

        x += Math.cos(lat) * Math.cos(lon);
        y += Math.cos(lat) * Math.sin(lon);
        z += Math.sin(lat);
    });

    const total = locations.length;

    x /= total;
    y /= total;
    z /= total;

    const centralLongitude = Math.atan2(y, x);
    const centralSquareRoot = Math.sqrt(x * x + y * y);
    const centralLatitude = Math.atan2(z, centralSquareRoot);

    return [toDegrees(centralLatitude), toDegrees(centralLongitude)];
}

function separateOverlappingPoints(points: Location[], offset = 0.0001) {
    const validPoints = points.filter((p) => p.lat !== null && p.lng !== null) as Location[];

    // group points by coordinates
    const groupedPoints: Record<string, Location[]> = validPoints.reduce((acc, point) => {
        const key = `${point.lat},${point.lng}`;
        (acc[key] ||= []).push(point);
        return acc;
    }, {} as Record<string, Location[]>);

    // adjust overlapping points
    const adjustedPoints = Object.values(groupedPoints).flatMap((group) =>
        group.length === 1
            ? group
            : group.map((point, index) => {
                  const angle = (2 * Math.PI * index) / group.length;
                  return {
                      ...point,
                      lat: point.lat! + offset * Math.cos(angle),
                      lng: point.lng! + offset * Math.sin(angle),
                  };
              })
    );

    // include points with null values
    return [...adjustedPoints, ...points.filter((p) => p.lat === null || p.lng === null)];
}

interface InnerMapProps {
    locations: Location[];
    center: [number, number]
}

function InnerMap({ locations, center } :InnerMapProps) {
    const map = useMap();

    useEffect(() => {
        map.flyTo({ lat: center[0], lng: center[1]})
    }, [center[0], center[1]])     

    return (
        <>
            <TileLayer
                // @ts-ignore
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {separateOverlappingPoints(locations).map(({ lat, lng, color }, i) => (
                <Marker key={i} lat={lat} lng={lng} color={color}/>
            ))}    
        </>
    )

}

function Map({ locations, zoom }: MapProps) {
    const center = getGeographicCenter(locations)
    
    return (
        <MapContainer
            // @ts-ignore
            center={center}
            zoom={zoom}
            zoomControl={false}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%" }}
        >
            <InnerMap locations={locations} center={center}/>
        </MapContainer>
    );
};

export default React.memo(Map);
