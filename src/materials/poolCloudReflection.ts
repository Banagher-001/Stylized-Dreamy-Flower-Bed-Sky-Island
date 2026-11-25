/** Two cloud silhouettes on a repeating sky plane, in local courtyard units. */
export const poolCloudReflectionGLSL = /* glsl */`
  uniform vec2 uPoolRearCloud;
  uniform vec2 uPoolNearCloud;
  // Height above the water, drift speed, repeat distance, and wave response.
  uniform vec4 uPoolCloudMotion;
  uniform vec3 uPoolCloudBody;
  uniform vec3 uPoolCloudEdge;

  float mergeCloudLobes(float a, float b) {
    float blend = max(.22 - abs(a - b), 0.0);
    return min(a, b) - blend * blend / .88;
  }

  float cloudLobe(vec2 p, vec2 center, vec2 radii, float slant) {
    vec2 offset = p - center;
    offset.y -= offset.x * slant;
    return length(offset / radii);
  }

  float rearCloudContour(vec2 p) {
    float cloud = cloudLobe(p, vec2(-.101, -.237), vec2(.672, .409), .224);
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(-.547, -.364), vec2(.453, .263), -.062));
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(.352, .104), vec2(.539, .429), .175));
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(-.187, .153), vec2(.485, .331), -.449));
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(.501, .396), vec2(.258, .195), .150));
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(-.633, .221), vec2(.164, .107), -.187));
    cloud = min(cloud, cloudLobe(p, vec2(.595, .689), vec2(.149, .078), .511));
    return min(cloud, cloudLobe(p, vec2(.180, .689), vec2(.156, .088), .112));
  }

  float nearCloudContour(vec2 p) {
    float cloud = cloudLobe(p, vec2(-.450, -.435), vec2(.266, .253), .586);
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(-.286, -.152), vec2(.383, .224), .374));
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(.152, .169), vec2(.383, .273), .249));
    cloud = mergeCloudLobes(cloud, cloudLobe(p, vec2(.465, .267), vec2(.328, .185), -.511));
    cloud = min(cloud, cloudLobe(p, vec2(-.380, .091), vec2(.125, .097), .249));
    return min(cloud, cloudLobe(p, vec2(.645, .530), vec2(.172, .097), .125));
  }

  vec2 cloudProfilePoint(vec2 sky, vec2 center, vec2 wind, float period) {
    vec2 p = sky - center;
    float forward = dot(p, wind);
    p -= wind * period * floor((forward + period * .5) / period);
    // Orient the painted shapes on the sky plane, independently of the current camera.
    vec2 axis = vec2(.986364, -.164577);
    return vec2(dot(p, axis), dot(p, vec2(-axis.y, axis.x)));
  }

  // The edge breakup and light pockets travel with each cloud.
  vec2 cloudOpacityAndBody(vec2 p, float aa, bool rear) {
    if (any(greaterThan(abs(p), vec2(1.29, 1.15)))) return vec2(0.0);
    vec2 distortion = vec2(
      artNoise(p * vec2(4.5, 4.2) + vec2(2.4, 7.1)),
      artNoise(p * vec2(3.2, 5.4) + vec2(9.2, 1.8))
    ) - .5;
    vec2 shaped = p + distortion * vec2(.20, .18);
    float contour = rear ? rearCloudContour(shaped) : nearCloudContour(shaped);
    float cut = (artNoise(p * vec2(13.3, 13.4) + vec2(8.4, 3.1)) - .52) * .23;
    float fringe = artNoise(p * vec2(23.7, 24.6) + vec2(1.8, 4.9));
    float brokenEdge = smoothstep(rear ? .71 : .58, .98, contour)
      * smoothstep(rear ? .54 : .41, .83, fringe) * (rear ? .40 : .51);
    float opacity = (1.0 - smoothstep(.80, 1.07 + aa, contour + cut)) * (1.0 - brokenEdge);
    float pockets = smoothstep(.34, .84, artNoise(p * vec2(2.7, 3.8) + vec2(3.0, 12.7)));
    float body = smoothstep(.36, .98, opacity) * (1.0 - pockets * .55);
    return vec2(opacity, body);
  }

  vec4 samplePoolClouds(vec2 surface, vec3 incident, vec2 tilt, vec2 wind, float aa) {
    vec2 wave = tilt * uPoolCloudMotion.w;
    vec3 direction = reflect(incident, normalize(vec3(wave.x, 1.0, wave.y)));
    if (direction.y <= .05) return vec4(0.0);
    float period = uPoolCloudMotion.z;
    float advance = mod(uPoolTime * uPoolCloudMotion.y, period);
    vec2 sky = surface + direction.xz * (uPoolCloudMotion.x / direction.y) - wind * advance;
    vec2 rear = cloudOpacityAndBody(cloudProfilePoint(sky, uPoolRearCloud, wind, period), aa, true);
    // A second thin cloud passes between the rear clouds, within the same full cycle.
    vec2 near = cloudOpacityAndBody(cloudProfilePoint(sky, uPoolNearCloud, wind, period * .5), aa, false);
    return vec4(rear.x, near.x, rear.y, near.y);
  }
`;
