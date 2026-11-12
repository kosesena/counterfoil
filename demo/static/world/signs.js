// The model batches static meshes by material. Mount opaque plates just ahead of
// the original lettering so the dashboard and both signs share the same artwork.
import * as THREE from "three";

export function mountStoreSigns(root, wordmark) {
  wordmark.colorSpace = THREE.SRGBColorSpace;
  const paper = new THREE.MeshBasicMaterial({ color: 0xf4ecdf });
  const ink = new THREE.MeshBasicMaterial({ map: wordmark, transparent: true, depthWrite: false });
  const aspect = wordmark.image.width / wordmark.image.height;

  function sign(x, y, z, width, height, markWidth) {
    const plate = new THREE.Mesh(new THREE.PlaneGeometry(width, height), paper);
    plate.position.set(x, y, z);
    const mark = new THREE.Mesh(new THREE.PlaneGeometry(markWidth, markWidth / aspect), ink);
    mark.position.z = 0.006;
    plate.add(mark);
    root.add(plate);
  }

  sign(0, 2.29, -4.72, 3.24, 1.18, 2.65);
  sign(-1.3, 0.56, -2.25, 1.08, 0.72, 0.88);
}
