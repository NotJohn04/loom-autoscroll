import { setup } from "@loomhq/record-sdk";
import { isSupported } from "@loomhq/record-sdk/is-supported";

const PUBLIC_APP_ID = "3f339f75-eb83-49c0-a7ad-6530f7a27542";
const BUTTON_ID = "loom-record-sdk-button";

export async function initLoom() {
  const { supported, error } = await isSupported();
  if (!supported) {
    console.warn("Loom not supported:", error);
    return;
  }

  const button = document.getElementById(BUTTON_ID);
  if (!button) return;

  const { configureButton } = await setup({ publicAppId: PUBLIC_APP_ID });
  const sdkButton = configureButton({ element: button });

  // expose the sdkButton to window so automation can control it:
  window.__loomSdkButton = sdkButton;

  sdkButton.on("recording-start", () => console.log("Recording started"));
  sdkButton.on("complete", () => console.log("Recording complete"));
}
initLoom();
