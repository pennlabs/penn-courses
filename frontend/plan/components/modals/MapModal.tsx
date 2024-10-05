import React, { useState, useEffect } from "react";
import { GeoLocation } from "../../types";
import {
    APIProvider,
    Map,
    Marker,
    useMap,
    useMapsLibrary,
} from "@vis.gl/react-google-maps";

interface MapModalProps {
    src: GeoLocation;
    tgt?: GeoLocation;
}

interface DirectionsProps {
    src: GeoLocation;
    tgt: GeoLocation;
}

const MapModal = ({ src, tgt }: MapModalProps) => {
    const { latitude: centerLat, longitude: centerLng } = tgt
        ? {
              latitude: (src.latitude + tgt.latitude) / 2,
              longitude: (src.longitude + tgt.longitude) / 2,
          }
        : src;

    return (
        <APIProvider
            apiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string}
        >
            <Map
                style={{ height: "300px" }}
                defaultCenter={{ lat: centerLat, lng: centerLng }}
                defaultZoom={15}
                gestureHandling={"greedy"}
                disableDefaultUI={true}
            >
                {tgt ? (
                    <Directions src={src} tgt={tgt} />
                ) : (
                    <Marker
                        position={{ lat: src.latitude, lng: src.longitude }}
                    />
                )}
            </Map>
        </APIProvider>
    );
};

function Directions({ src, tgt }: DirectionsProps) {
    const map = useMap();
    const routesLibrary = useMapsLibrary("routes");
    const [directionsService, setDirectionsService] = useState<
        google.maps.DirectionsService
    >();
    const [directionsRenderer, setDirectionsRenderer] = useState<
        google.maps.DirectionsRenderer
    >();
    const [routes, setRoutes] = useState<google.maps.DirectionsRoute[]>([]);

    const leg = routes[0]?.legs[0];

    useEffect(() => {
        if (!routesLibrary || !map) return;
        setDirectionsService(new routesLibrary.DirectionsService());
        setDirectionsRenderer(new routesLibrary.DirectionsRenderer({ map }));
    }, [routesLibrary, map]);

    useEffect(() => {
        if (!directionsService || !directionsRenderer) return;

        directionsService
            .route({
                origin: `${src.latitude}, ${src.longitude}`,
                destination: `${tgt.latitude}, ${tgt.longitude}`,
                travelMode: google.maps.TravelMode.WALKING,
                provideRouteAlternatives: false,
            })
            .then((response) => {
                directionsRenderer.setDirections(response);
                setRoutes(response.routes);
            });
    }, [directionsService, directionsRenderer]);

    if (!leg) return null;

    return (
        <div style={{ position: "absolute" }}>
            <h2>{leg.duration?.text}</h2>
        </div>
    );
}

export default MapModal;
